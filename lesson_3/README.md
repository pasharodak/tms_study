Structures
├── Атрибуты:
│   ├── length: list | int
│   ├── data_type: type
│   └── _data: str | int | list | dict
├── Методы:
│   ├── search_elem(position: int | list) → Any
│   ├── __filling(condition) → Any
│   ├── get_data → Any  [@property]
│   ├── set_data(position, value) → Any  [@property]  ❌ (не используется)
│   ├── __add__(other: Structures) → Structures
│   └── __mul__(numb: int) → Structures
│
├── OneDimensional : Structures
│   ├── search_elem(position: int) → Any
│   ├── get_data → list | str  [@property]
│   └── set_data(position: int, value: Any) → Any
│
│   ├── StrStructures : OneDimensional
│   │   ├── __filling(length: int) → str
│   │   ├── __add__(other: StrStructures) → StrStructures
│   │   ├── __mul__(numb: int) → StrStructures
│   │   ├── set_data(position: int, value: str) → str
│   │   └── get_data → str  [@property]
│
│   └── ListStructures : OneDimensional
│       ├── __filling(length: int) → list[int]
│       ├── __add__(other: ListStructures) → ListStructures
│       ├── __mul__(numb: int) → ListStructures
│       ├── set_data(index: int, value: int) → list[int]
│       └── get_data → list[int]  [@property]
│
└── TwoDimensional : Structures
    ├── __init__(row: int, col: int, data_type: type, data: list[list] | None)
    └── (базовая реализация без операций)

    └── MatrixStructures : TwoDimensional
        ├── __init__(rows: int, cols: int, data_type: type, data: list[list[int]] = [])
        ├── __filling(length: list[int]) → list[list[int]]
        ├── __add__(other: MatrixStructures) → MatrixStructures
        ├── __mul__(numb: int) → MatrixStructures
        ├── get_data → list[list[int]]  [@property]
        ├── search_elem(row: int, col: int) → int
        └── set_data(row: int, col: int, value: int) → list[list[int]]
