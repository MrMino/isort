import re
from typing import Any, Callable, Iterable, List, Optional

from .settings import Config

_import_line_intro_re = re.compile("^(?:from|import) ")
_import_line_midline_import_re = re.compile(" import ")


def module_key(
    module_name: str,
    config: Config,
    sub_imports: bool = False,
    ignore_case: bool = False,
    section_name: Optional[Any] = None,
    straight_import: Optional[bool] = False,
) -> str:
    match = re.match(r"^(\.+)\s*(.*)", module_name)
    if match:
        sep = " " if config.reverse_relative else "_"
        module_name = sep.join(match.groups())

    prefix = ""
    if ignore_case:
        module_name = str(module_name).lower()
    else:
        module_name = str(module_name)

    if sub_imports and config.order_by_type:
        if module_name in config.constants:
            prefix = "A"
        elif module_name in config.classes:
            prefix = "B"
        elif module_name in config.variables:
            prefix = "C"
        elif module_name.isupper() and len(module_name) > 1:  # see issue #376
            prefix = "A"
        elif module_name in config.classes or module_name[0:1].isupper():
            prefix = "B"
        else:
            prefix = "C"
    if not config.case_sensitive:
        module_name = module_name.lower()

    length_sort = (
        config.length_sort
        or (config.length_sort_straight and straight_import)
        or str(section_name).lower() in config.length_sort_sections
    )
    _length_sort_maybe = (str(len(module_name)) + ":" + module_name) if length_sort else module_name
    return f"{module_name in config.force_to_top and 'A' or 'B'}{prefix}{_length_sort_maybe}"


def section_key(
    line: str,
    case_sensitive: bool,
    honor_case_in_force_sorted_sections: bool,
    order_by_type: bool,
    force_to_top: List[str],
    lexicographical: bool = False,
    length_sort: bool = False,
    reverse_relative: bool = False,
    group_by_package: bool = False,
) -> str:
    section = "B"

    if reverse_relative and line.startswith("from ."):
        match = re.match(r"^from (\.+)\s*(.*)", line)
        if match:  # pragma: no cover - regex always matches if line starts with "from ."
            line = f"from {' '.join(match.groups())}"
    if group_by_package and line.strip().startswith("from"):
        line = line.split(" import", 1)[0]

    if lexicographical:
        line = _import_line_intro_re.sub("", _import_line_midline_import_re.sub(".", line))
    else:
        line = re.sub("^from ", "", line)
        line = re.sub("^import ", "", line)
    if line.split(" ")[0] in force_to_top:
        section = "A"
    # * If honor_case_in_force_sorted_sections is true, and case_sensitive and
    #   order_by_type are different, only ignore case in part of the line.
    # * Otherwise, let order_by_type decide the sorting of the whole line. This
    #   is only "correct" if case_sensitive and order_by_type have the same value.
    if honor_case_in_force_sorted_sections and case_sensitive != order_by_type:
        split_module = line.split(" import ", 1)
        if len(split_module) > 1:
            module_name, names = split_module
            if not case_sensitive:
                module_name = module_name.lower()
            if not order_by_type:
                names = names.lower()
            line = " import ".join([module_name, names])
        elif not case_sensitive:
            line = line.lower()
    elif not order_by_type:
        line = line.lower()

    return f"{section}{len(line) if length_sort else ''}{line}"


def naturally(to_sort: Iterable[str], key: Optional[Callable[[str], Any]] = None) -> List[str]:
    """Returns a naturally sorted list"""
    if key is None:
        key_callback = _natural_keys
    else:

        def key_callback(text: str) -> List[Any]:
            return _natural_keys(key(text))  # type: ignore

    return sorted(to_sort, key=key_callback)


def _atoi(text: str) -> Any:
    return int(text) if text.isdigit() else text


def _natural_keys(text: str) -> List[Any]:
    return [_atoi(c) for c in re.split(r"(\d+)", text)]
