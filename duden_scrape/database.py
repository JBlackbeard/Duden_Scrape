import sqlite3
import logging

logger = logging.getLogger(__name__)


class DatabaseManager():
    def __init__(self, database_filename):
        self.connection = sqlite3.connect(database_filename)
        


    def __del__(self):
        self.connection.close()

    def _execute(self, statement, values=None):
        with self.connection:
            self.connection.execute("PRAGMA foreign_keys = ON")
            cursor = self.connection.cursor()
            logger.debug(f"data: {statement}", exc_info=True)
            cursor.execute(statement, values or [])
            return cursor

    def create_table(self, table_name, columns, references={}, cascade_delete=False):
        """
        columns: dict with {column_name: data_type}
        references: dict with {foreign_key: TABLE_NAME(reference)}
        """
        columns_with_types = [
            f"{column_name} {data_type}"
            for column_name, data_type in columns.items()
        ]
        foreign_keys = [
            f",FOREIGN KEY ({foreign_key}) REFERENCES {reference}"
            for foreign_key, reference in references.items()
        ]
        if cascade_delete:
            cascade_delete = "ON DELETE CASCADE"
        else:
            cascade_delete = ""
        self._execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name}
            ({", ".join(columns_with_types)}
            {" ".join(foreign_keys)}
            {cascade_delete} );
            """
        )
    
    def drop_table(self, table_name):
        try:
            self._execute(f"DROP TABLE {table_name};")
        except sqlite3.OperationalError:
            print(f"Table {table_name} does not exist and could not be dropped")

    def add(self, table_name, data):
        logger.debug(f"data: {data}", exc_info=True)
        placeholders = ", ".join("?" * len(data))
        column_names = ", ".join(data.keys())
        column_values = tuple(data.values())

        self._execute(
            f"""
            INSERT INTO {table_name}
            ({column_names})
            VALUES ({placeholders});
            """,
            column_values
        )

    def select(self, column_name, table_name, criteria=None, order_by=None, limit=None):
            criteria = criteria or {}

            query = f'SELECT {column_name} FROM {table_name}'

            if criteria:
                placeholders = [f'{column} = ?' for column in criteria.keys()]
                select_criteria = ' AND '.join(placeholders)
                query += f' WHERE {select_criteria}'

            if order_by:
                query += f' ORDER BY {order_by}'

            if limit:
                query += f" LIMIT {limit}"

            return self._execute(
                query,
                tuple(criteria.values()),
            )

    def delete(self, table_name, criteria):
        placeholders = [f'{column} = ?' for column in criteria.keys()]
        delete_criteria = ' AND '.join(placeholders)
        self._execute(
            f'''
            DELETE FROM {table_name}
            WHERE {delete_criteria};
            ''',
            tuple(criteria.values()),
        )

    def is_empty(self, table_name):
        return self.select("*", table_name, limit="1").fetchone() == None
        
    
    def get_max_id(self, table_name):
        return self.select("id", table_name, criteria={"id": self.select("id", table_name, order_by="id desc", limit="1").fetchone()[0]}).fetchone()[0]