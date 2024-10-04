# ducktools.env
# MIT License
# 
# Copyright (c) 2024 David C Ellis
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# This is a minimal object/database wrapper for ducktools.classbuilder
# Execute the class to see examples of the methods that will be generated

from ducktools.classbuilder import (
    GeneratedCode,
    MethodMaker,
    builder,
    make_annotation_gatherer,
)

from ducktools.classbuilder.prefab import (
    PREFAB_FIELDS,
    Attribute,
    as_dict,
    eq_maker,
    get_attributes,
    init_maker,
    repr_maker,
)


TYPE_MAP = {
    None: "NULL",
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bytes: "BLOB",
    list[str]: "TEXT"  # lists of strings are converted to delimited strings
}


class SQLAttribute(Attribute):
    """
    A Special attribute for SQL tables

    :param unique: Should this field be unique in the table
    :param internal: Should this field be excluded from the table
    """
    primary_key: bool = False
    unique: bool = False
    internal: bool = False

    def validate_field(self):
        super().validate_field()
        if self.primary_key and self.unique:
            raise AttributeError("Primary key fields are already unique")


def get_sql_fields(cls) -> dict[str, SQLAttribute]:
    return get_attributes(cls)  # type: ignore


annotation_gatherer = make_annotation_gatherer(SQLAttribute)


def flatten_list(strings: list[str], *, delimiter=";") -> str:
    return delimiter.join(strings)


def separate_list(string: str, *, delimiter=";") -> list[str]:
    return string.split(delimiter)


def create_table_generator(cls: type, funcname: str = "create_table") -> GeneratedCode:
    table_name = getattr(cls, "TABLE_NAME")
    fields = get_sql_fields(cls)

    sql_field_list = []
    for name, field in fields.items():
        # skip internal fields
        if getattr(field, "internal", False):
            continue

        field_type = TYPE_MAP[field.type]
        if field.primary_key:
            constraint = " PRIMARY KEY"
        elif field.unique:
            constraint = " UNIQUE"
        else:
            constraint = ""

        sql_field_list.append(f"{name} {field_type}{constraint}")

    field_info = ", ".join(sql_field_list)
    sql_template = f"\"CREATE TABLE {table_name}({field_info})\""

    code = (
        f"@staticmethod\n"
        f"def {funcname}(con):\n"
        f"    con.execute({sql_template})\n"
    )
    globs = {}

    return GeneratedCode(code, globs)


def insert_row_generator(cls: type, funcname: str = "insert_row") -> GeneratedCode:
    table_name = getattr(cls, "TABLE_NAME")
    fields = get_sql_fields(cls)

    columns = ", ".join(
        f":{name}" for name, field in fields.items()
        if not field.internal
    )

    valid_fields = {name for name, field in fields.items() if not field.internal}
    pk = cls.PRIMARY_KEY

    sql_statement = f"INSERT INTO {table_name} VALUES({columns})"

    globs = {
        "flatten_list": flatten_list,
        "as_dict": as_dict,
        "valid_fields": valid_fields,
    }

    code = (
        f"def {funcname}(self, con):\n"
        f"    raw_values = as_dict(self)\n"
        f"    processed_values = {{\n"
        f"        name: flatten_list(value) if isinstance(value, list) else value\n"
        f"        for name, value in raw_values.items()\n"
        f"        if name in valid_fields\n"
        f"    }}\n"
        f"    result = con.execute(\"{sql_statement}\", processed_values)\n"
        f"    if self.{pk} is None:\n"
        f"        self.{pk} = result.lastrowid\n"
    )

    return GeneratedCode(code, globs)


def update_row_generator(cls: type, funcname: str = "from_row"):
    table_name = getattr(cls, "TABLE_NAME")
    fields = get_sql_fields(cls)

    valid_fields = {name for name, field in fields.items() if not field.internal}

    globs = {
        "flatten_list": flatten_list,
        "as_dict": as_dict,
        "valid_fields": valid_fields,
    }

    sql_statement = f"UPDATE {table_name} SET {{set_columns}} WHERE {{search_condition}}"

    code = (
        f"def {funcname}(self, con, columns):\n"
        f"    if invalid_columns := (set(columns) - valid_fields):\n"
        f"        raise ValueError(f'Invalid fields: {{invalid_columns}}')\n"
        f"    raw_values = as_dict(self)\n"
        f"    processed_values = {{\n"
        f"        name: flatten_list(value) if isinstance(value, list) else value\n"
        f"        for name, value in raw_values.items()\n"
        f"        if name in valid_fields\n"
        f"    }}\n"
        f"    set_columns = ', '.join(f\"{{name}} = :{{name}}\" for name in columns)\n"
        f"    search_condition = f\"{cls.PRIMARY_KEY} = :{cls.PRIMARY_KEY}\"\n"
        f"    con.execute(f\"{sql_statement}\", processed_values)\n"
    )

    return GeneratedCode(code, globs)


def delete_row_generator(cls: type, funcname: str = "delete_row") -> GeneratedCode:
    pk = cls.PRIMARY_KEY
    sql_statement = f"DELETE FROM {cls.TABLE_NAME} WHERE {pk} = :{pk}"
    code = (
        f"def {funcname}(self, con):\n"
        f"    values = {{\"{pk}\": self.{pk}}}\n"
        f"    con.execute(\"{sql_statement}\", values)\n"
    )
    globs = {}
    return GeneratedCode(code, globs)


def row_factory_generator(cls: type, funcname: str = "row_factory") -> GeneratedCode:
    split_rows = {
        name
        for name, field in get_sql_fields(cls).items()
        if field.type == list[str]
    }

    code = (
        f"@classmethod\n"
        f"def {funcname}(cls, cursor, row):\n"
        f"    fields = [column[0] for column in cursor.description]\n"
        f"    kwargs = {{\n"
        f"        key: separate_list(value) if key in split_rows else value\n"
        f"        for key, value in zip(fields, row)\n"
        f"    }}\n"
        f"    return cls(**kwargs)\n"
    )
    globs = {
        "split_rows": split_rows,
        "separate_list": separate_list,
    }
    return GeneratedCode(code, globs)


create_table_maker = MethodMaker("create_table", create_table_generator)
insert_row_maker = MethodMaker("insert_row", insert_row_generator)
update_row_maker = MethodMaker("update_row", update_row_generator)
delete_row_maker = MethodMaker("delete_row", delete_row_generator)
row_factory_maker = MethodMaker("row_factory", row_factory_generator)

methods = {
    init_maker,
    repr_maker,
    eq_maker,
    create_table_maker,
    insert_row_maker,
    update_row_maker,
    delete_row_maker,
    row_factory_maker,
}


def sqlclass(table_name: str):
    def class_maker(cls):
        setattr(cls, "TABLE_NAME", table_name)
        builder(cls, gatherer=annotation_gatherer, methods=methods, flags={"kw_only": True})

        # Need to set PREFAB_FIELDS for as_dict to recognise the class
        fields = get_sql_fields(cls)
        setattr(cls, PREFAB_FIELDS, list(fields.keys()))

        primary_key = None
        for name, field in fields.items():
            if field.primary_key:
                primary_key = name
                break

        if primary_key is None:
            raise AttributeError("sqlclass *must* have one primary key")

        if sum(1 for f in fields.values() if f.primary_key) > 1:
            raise AttributeError("sqlclass *must* have **only** one primary key")

        setattr(cls, "PRIMARY_KEY", primary_key)

        return cls

    return class_maker


def demoing():
    @sqlclass("demo_table")
    class Demo:
        id: int = SQLAttribute(primary_key=True)
        path: str = SQLAttribute(unique=True)
        spec_hashes: list[str]

    print(create_table_generator(Demo).source_code)
    print(insert_row_generator(Demo).source_code)
    print(update_row_generator(Demo).source_code)
    print(delete_row_generator(Demo).source_code)
    print(row_factory_generator(Demo).source_code)


if __name__ == "__main__":
    demoing()
