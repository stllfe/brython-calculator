from typing import Union, List
from enum import IntEnum, Enum


class Operation(Enum):
    Sum = '+'
    Divide = '/'
    Multiply = '*'
    Subtract = '-'

    def __str__(self):
        return self.value


class CastToNumberError(Exception):
    pass


class InputState(IntEnum):
    Number = 0
    Operation = 1


class TextAlign(Enum):
    Left = '<'
    Right = '>'
    Center = '^'


class Calculator:

    def __init__(self, precision: int = 6):
        self._precision = precision
        self._expression = str()
        self._state = None

        self._set_initial()

    # Public interface methods

    def reset(self):
        self._set_initial()

    def equal(self) -> float:
        """
        Evaluates internal expression and returns the result.
        :return: float
        """

        reduced = _strip_operations(self._expression)
        precise = float(eval(reduced))
        rounded = round(precise, self._precision)
        cleaned = _try_cast_to_int(rounded)

        self._set_initial(cleaned)
        return cleaned

    def display(self) -> str:
        """
        Returns pretty string for current expression.
        :return: pretty string
        """

        def _prettify(value: str):

            if _is_number(value):
                value = _to_number(value)
                return f'({value})' if value < 0 else str(value)

            return value

        return ' '.join(map(_prettify, self._expression.split())).strip()

    @property
    def expression(self) -> str:
        return self._expression

    def add_operation(self, value: str):
        operation = _to_operation(value)
        as_string = str(operation)

        if self.is_number_state():
            if operation is Operation.Subtract and self.can_negate():
                # Treat subtraction as negation
                self._append(as_string, align=TextAlign.Left, padding=1, replace_initial=True)
            else:
                self._switch_state()
                self.add_operation(value)

        elif self.is_operation_state():

            # todo:
            #  It still messes up replacing and adding operations after negation ...
            #  I should have just written a dumb elif tree instead

            two_operations_already = all(map(_is_operation, self.get_last(2)))

            # todo: Should be a better way to handle it
            if two_operations_already:
                print('Found two operations in a row')
                self.undo()

            if self.is_last_operation():
                self._update_last(as_string)
                self._switch_state()
                print(f'Changed `{self.get(-1)}` to `{as_string}`')

            elif self.is_last_number():
                self._append(as_string)
                self._switch_state()
                print(f'Added operation `{as_string}`')

    def add_number(self, value: str):

        if self.is_operation_state():
            self._switch_state()
            self.add_number(value)

        elif self.is_number_state():
            self._append(value, padding=0, replace_initial=True)

    def dot(self):
        if self.is_number_state() and self.can_put_dot():
            self._append('.', padding=0)
        else:
            self.gracefully_do_nothing()

    def undo(self):
        print('Reverting one step back')
        self._remove_last()

        if self.is_empty():
            self._set_initial()

    def get_last(self, num_items: int = 2) -> List[str]:
        items = map(self.get, range(-num_items, 0))
        return list(filter(lambda val: len(val) > 0, items))

    def get(self, index: int, default=str()):
        try:
            return self._expression.strip().split()[index]
        except IndexError:
            return default

    def clear(self):
        self._expression = str()

    def gracefully_do_nothing(self):
        # It does what it does ...
        pass

    def can_put_dot(self):

        if self.is_last_number():
            return isinstance(_to_number(self.get(-1)), int)

        return False

    def can_negate(self):

        if self.is_initial():
            return True

        if self.is_last_operation():
            # If negation is not already there
            return _to_operation(self.get(-1)) is not Operation.Subtract

        if self.is_last_number():
            # If number has already been printed negation is not allowed
            return False

        raise RuntimeError("Ambiguous state!")

    def is_number_state(self):
        return self._state is InputState.Number

    def is_operation_state(self):
        return self._state is InputState.Operation

    def is_last_operation(self):
        return _is_operation(self.get(-1))

    def is_last_number(self):
        return _is_number(self.get(-1))

    def is_empty(self) -> bool:
        return len(self._expression) == 0

    def is_initial(self) -> bool:
        return self._expression == str(0)

    # Service methods

    def _append(self, value: str, align: TextAlign = TextAlign.Center, padding: int = 3, replace_initial: bool = False):
        formatted = '{:{a}{p}}'.format(value, a=align.value, p=padding)

        if self.is_initial() and replace_initial:
            self._update_last(formatted.lstrip())
        else:
            self._expression += formatted

    def _pop(self):
        items = self._expression.split()
        self._expression = ' '.join(items[:-1])
        return items.pop()

    def _remove_last(self):
        if self.is_last_number():
            self._update_last('')
        else:
            self._pop()

    def _update_last(self, value: str):
        r_index = self._expression.rindex(self.get(-1))
        padding = self._expression[r_index:].count(' ')
        updated = self.get(-1)[:-1] + value + ' ' * padding

        self._expression = ' '.join(self._expression.split()[:-1] + [updated])

    def _switch_state(self):
        self._state = InputState(not self._state)
        print(f'Switched to `{self._state.name}`')

    def _set_initial(self, initial_value: Union[float, str] = 0):
        print(f'Entering initial state with number `{initial_value}`')
        self._state = InputState.Number
        self.clear()
        self.add_number(str(initial_value))


def _is_operation(value: str):
    try:
        _to_operation(value)
        return True
    except NotImplementedError:
        return False


def _to_number(value: str):
    try:
        return _try_cast_to_int(float(value))
    except (TypeError, ValueError) as e:
        raise CastToNumberError(f"Can't convert `{value}` to number. \n{e}")


def _to_operation(value: str):
    for operation in Operation:
        if value == operation.value:
            return operation

    raise NotImplementedError(f"Operation `{value}` has no handler candidate!")


def _strip_operations(expression: str):
    if len(expression) == 0:
        return expression

    while _is_operation(expression[-1]):
        expression = expression[:-1]

    return expression


def _is_number(value: str):
    try:
        _to_number(value)
        return True
    except CastToNumberError:
        return False


def _try_cast_to_int(value: (float, int)):
    return int(value) if float(value).is_integer() else value
