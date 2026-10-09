from django import forms


class NumericInput(forms.TextInput):
    """A text input with a numeric keypad.

    Browsers change a focused number input when the page scrolls, so integer
    fields use this instead. Django still validates the value as an integer.
    """

    def __init__(self, attrs=None):
        super().__init__({"inputmode": "numeric", "pattern": "[0-9]*", **(attrs or {})})


class NumericInputsMixin:
    """Render every integer field on the form with NumericInput."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field, forms.IntegerField):
                field.widget = NumericInput()
