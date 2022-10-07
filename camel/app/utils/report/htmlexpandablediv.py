from typing import List, Tuple

from yattag import Doc

from camel.app.utils.report.htmlelement import HtmlElement


class HtmlExpandableDiv(HtmlElement):
    """
    This class contains a div that can be shown / hidden by clicking.
    The jquery source code needs to be included in the HTML report, otherwise this will not work!
    """

    SCRIPT_TEMPLATE = """
    $(document).ready(function(){{
        $('#content-{id_}').hide()
    }});
    $('input:checkbox#toggle-{id_}').change(
        function() {{
            if ($(this).is(':checked')) {{
                $('#content-{id_}').show()
            }} else {{
                $('#content-{id_}').hide()
            }}
        }});        
    """

    def __init__(self, id_: str, label: str, attributes: List[Tuple[str, str]]=None):
        """
        Initializes an expandable div.
        :param id_: Id of the element that is hidden / shown
        :param label: Label that is used
        :param attributes: Attributes
        """
        super().__init__('div', attributes=attributes)
        self._id = id_
        self._label = label

    def to_html(self) -> str:
        """
        Converts this element to HTML code. A novel Doc() instance is created in order to nest the content of this
        elements Doc() inside the tag associated with this HtmlExpandableDiv.
        :return: HTML code
        """
        doc, tag, text = Doc().tagtext()
        with tag('div'):
            with tag('p'):
                with tag('b'):
                    text('Show / hide {}'.format(self._label))
            with tag('label', klass='switch'):
                doc.stag('input', type='checkbox', id='toggle-{}'.format(self._id))
                with tag('span', klass='slider round'):
                    text('')
            with tag('div', id='content-{}'.format(self._id)):
                doc.asis(self._doc.getvalue())
            with tag('script', type='text/javascript'):
                text(HtmlExpandableDiv.SCRIPT_TEMPLATE.format(id_=self._id))
        return doc.getvalue()
