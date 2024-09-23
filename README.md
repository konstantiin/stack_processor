# Translator + processor model for Assembler

- Лучинкин Константин Сергеевич. Группа: P3230
- ` lisp -> asm | stack | harv | hw | instr | binary -> struct | stream | port | cstr | prob2 | cache `
- Базовый вариант

  
## Язык программирования
### Синтаксис:
 

### Семантика:  


### Типизация, виды литералов


## Организация памяти

- Гарвардская архитектура
- Резмер машинного слова:
  - Память данных - 32 бит;
  - Память команд - 32 бит.
- Адресации:
  - Прямая абсолютная (у команд `jump`, `js`, `jns`)
  - Косвенная (у команд `ld`, `mov` один из операндов является указателем на ячейку памяти)

```
       Registers
+------------------------------+
| TOS                          |
+------------------------------+
| Stack Registers              |
|    ...                       |
+------------------------------+
| SP, IP, SC                   |
+------------------------------+

       Program memory
+------------------------------+
| 00 :      start_instr        |
| ...                          |
| ...                          |
+------------------------------+

          Data memory
+------------------------------+
| 00  : var1                   |
| 01  : var2                   |
| 03  :....                    |
+------------------------------+

```


## Система команд

**Особенности процессора:**
- Машинное слово -- знаковое 32-ух битное число;
- Доступ памяти осуществляется через указатель в `TOS`.
- Устройство ввода-вывод: port-mapped
- Поток управления: 
  - Инкрементирование `PC`;
  - Условный/безусловный переход;


Из транслятора выходят команды в формате: 4 бит на опкод + 28 на аргумент. В Control Unit опкод команды переводится в управляющие сигналы (отображение команды в опкод можно посмотреть в [isa.py](./isa.py))

**Набор инструкций:**
Приведена мнемоническая запись для удобства чтения
``` asm
push val;     push val on stack
pop;          pop stack

mov;          value at [tos] to tos
ld;           saves tos-1 at [tos]

out;          sends tos to stdout
in;           reads one byte to tos  

jns addr;     jumps to addr if tos >= 0
jz addr;      jumps to addr if tos == 0
jump addr;     jumps to addr

add;          tos-1 + tos -> tos
sub;          tos-1 - tos -> tos
```
## Транслятор

Интерфейс командной строки: translator.py <input_file> <target_file>

Реализация транслятора: [translator.py](./translator.py)

## Модель процессора


Интерфейс командной строки: `python3 machine.py <code_file> <input_file>`

Реализация: [machine.py](./machine.py)

### DataPath

![alt text](scheme/data-path.svg "DataPath")

Регистры:
- `STACK` -- стековые регистры  
- `TOS` -- top of the stack - значение вершины стэка;
- `SP`  -- stack pointer - указатель на вершину стека в стековых регистрах

Сигналы:
- `latch_sp` -- защелкивает `SP`
- `latch_st` -- защелкивает `STACK`.
- `latch_tos` -- защелкивает `TOS` В регистр `TOS` данные могу прийти из:
  - АЛУ
  - стековых регитров
  - памяти данных
  - устройства ввода/вывода
  - control unit (если в инструкции есть операнд)
- `in/out` -- сигнал для устройства ввода/вывода
- `w/r` -- сигнал для памяти (запись, чтение данных)
- `sel_st` -- увеличить `SP` или уменьшить
- `alu` -- сигнал АЛУ выполнить сложение или вычитание


## Control Unit
  ![alt text](scheme/control-unit.svg "DataPath")
Регистры:
- `IP` -- стековые регистры  
- `SC` -- step counter хранит номер такта

Сигналы:
- `latch_ip` -- защелкивает `IP`
- `sel_next` -- выбор следующей инструкции
## Тестирование

Тестирование реализовано через golden тесты.  
Директория с тестами: [golden](./golden/)  
Исполняемый файл: [golden_test.py](./golden_test.py)

### CI:

``` yml
name: Python CI

on:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.9

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Run tests and collect coverage
        run: |
          poetry run coverage run -m pytest .
          poetry run coverage report -m
        env:
          CI: true

  lint:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.9

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Check code formatting with Ruff
        run: poetry run ruff format --check .

      - name: Run Ruff linters
        run: poetry run ruff check .
```

### Отчет на примере Hello, world



Отформатированные машинный код (человекочитаемый не бинарный вид):

``` python

```

Отформатированные данные:

```
[72, 101, 108, 108, 111, 44, 32, 119, 111, 114, 108, 100, 33, 0]
```

Журнал (не весь):

```
```

### Результаты

```text
| ФИО                           | алг            | LoC | code инстр. | инстр. | такт. |
| Лучинкин Константин Сергееич  | cat            |   |            |      |    |
| Лучинкин Константин Сергееич  | hello_world    |   |           |     |    |
| Лучинкин Константин Сергееич  | hello_alice    |   |           |     |   |
| Лучинкин Константин Сергееич  | prob2          |  |           |     |   |
```

### prob2
Посчитать сумму четных чисел Фибоначчи до 4 миллионов.  

Поймем, что каждое третье число Фибоначчи, начиная с 2 - четное и других четных нет. А также, что текущее четное число Фибоначчи можно выразить из предыдущих по формуле: $F_n = F_{n-1} + F_{n-2} = 2*F_{n-2} + F_{n-3} = 3F_{n-3} + 2*F_{n-4} = 3F_{n-3} + F_{n-5} + F_{n-4} + F_{n-6} =  F_{n - 3} + F_{n - 6}$

Тогда посчитаем последовательность в цикле, сложим результат в переменую.


``` lisp

```