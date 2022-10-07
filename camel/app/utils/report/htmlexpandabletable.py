import string
from typing import List, Optional

import random

from camel.app.utils.report.htmlbase import HtmlBase


class HtmlExpandableTable(HtmlBase):
    """
    Table that shows a fixed number of rows, but can show / hide the full content.
    """

    SCRIPT_TEMPLATE = """
    $(document).ready(function() {{
        var rowsExtra = $('table#{id_} tr').filter('.extra');
        var rowShowAll = $('table#{id_} tr.rowShowAll');
        rowsExtra.hide();
        
        $('#showAll_{id_}').click(function() {{
            rowShowAll.hide();
            rowsExtra.show();
        }});
        
        $('#showPreviewOnly_{id_}').click(function() {{
            rowShowAll.show();
            rowsExtra.hide();
        }});
    }});
    """

    def __init__(self, data: List[List], columns: List[str], nb_rows_shown: int = 5, id_: Optional[str] = None,
                 class_='data') -> None:
        """
        Initializes the table.
        :param data: Table data
        :param columns: Table column names
        :param nb_rows_shown: Number of rows shown
        :param id_: Unique id for in HTML, if not set a random one is generated
        :param class_: HTML table class
        """
        super().__init__()
        self._id = HtmlExpandableTable.create_random_id() if id_ is None else id_
        with self.get_tag('table', [('class', class_), ('id', self._id)]):
            # Table header
            if columns is not None:
                self._add_table_header(columns)

            # Table content
            for index, row in enumerate(data):
                class_ = 'extra' if index > nb_rows_shown else None
                self._add_table_row(row, [('class', class_)] if class_ else None)

            # Add control buttons
            if len(data) > nb_rows_shown:
                buttons = [
                    {'text': f'Show all ({len(data)})', 'id': 'showAll', 'row_class': 'rowShowAll'},
                    {'text': f'Only show first {nb_rows_shown} rows', 'id': 'showPreviewOnly', 'row_class': 'extra'},
                ]
                for button in buttons:
                    attr_row = [('class', button['row_class'])]
                    with self.get_tag('tr', attr_row):
                        with self.get_tag('td', [('colspan', str(len(columns)))]):
                            with self.get_tag('button', attributes=[('id', f"{button['id']}_{self._id}")]):
                                self.add_text(button['text'])

        # Script to hide / show content
        if len(data) > nb_rows_shown:
            with self.get_tag('script', [('type', 'text/javascript')]):
                self.add_text(HtmlExpandableTable.SCRIPT_TEMPLATE.format(id_=self._id))

    @staticmethod
    def create_random_id(size: int = 8) -> str:
        """
        Creates a random id.
        :param size: Size of the random string
        :return: Random id
        """
        return ''.join(random.choices(string.ascii_lowercase, k=size))
