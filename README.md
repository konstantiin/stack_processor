# Translator + processor model for Assembler

- Лучинкин Константин Сергеевич. Группа: P3230
- ` lisp -> asm | stack | harv | hw | instr | binary -> struct | stream | port | cstr | prob2 | cache `
- Базовый вариант

  
## Язык программирования
### Синтаксис:
``` ebnf
<program> ::= <statement>+
<statement> ::= <statement_no_defun> | <defun> 

<statement_no_defun> ::= <variable> | <func_call>

<func_call> ::= "(" <fname> <pass_args>* ")"
<fname> ::= <name> | "<" | "<=" | "+" | "*"
<variable> ::= "(" <name> ")"
<defun> ::= "(defun " <name> "(" <args> ")" <statement_no_defun>+ ")"
<args> ::=  <name>? ("," <name>)*
<pass_args> ::= <statement_no_defun> | <name> | <number>
<number> ::= [-2^27; 2^27 - 1]
<name> ::= (<letter_or_>)+
<letter_or_> ::= <letter> | ("_")
<letter> ::= [a-z] | [A-Z]
```

### Семантика: 
- `(defun fname(arg1, arg2, ..., argn) ())` определяет функцию с именем `fname` и аргументами `arg1`, `arg2..argn` 
- `+`, `*`, `-` выполняет соотвествующую арифметическую операцию
- `<`, `<=` если условие верно возвращает отрицательное число, иначе положительное (по сути вычитание)
- `(setq name val)` присваевает переменной `name` значение `val`
- `(read)` возвращвет адресс прочитанной строки(адресс первого символа)
- `(printi number)` выводит число
- `(prints str)` выводит строку
- `(var_name)` возвращает значение переменной `var_name`
- `(if (cond) (var1) (var2))` если `(cond)` истинно выполняет `(var1)`, иначе  `(var2)`
- `(when (cond) (var1))` если `(cond)` истинно выполняет `(var1)`, иначе не выполняет
- `(loop ...)` цикл. Чтобы выйти из цикла нужно вызвать `break`
- `(break)`- инструкция для выхода из цикла

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
  - Инкрементирование `IP`;
  - Условный/безусловный переход;


Из транслятора выходят команды в формате: 4 бит на опкод + 28 на аргумент. В Control Unit опкод команды переводится в управляющие сигналы (отображение команды в опкод можно посмотреть в [isa.py](./isa.py))

**Набор инструкций:**
Приведена мнемоническая запись для удобства чтения
``` asm
push val;     push val on stack
pop;          pop stack

mov;          value at [tos] to tos
ld;           saves tos-1 at [tos]

outc;          sends tos to stdout(as char)
outi;          sends tos to stdout(as int)

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

Трансляци состоит из прпроцессора(удаление комментариев), инлайнинга(на уровне языка рекурсия не поддерживается, хотя на уровне команд реализоват можно) и энкодера, который транслирует программу в машинный код.
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
- `in/outc/outi` -- сигнал для устройства ввода/вывода (передаётся порт соответсвующего устройства ввода вывода)
- `w/r` -- сигнал для памяти (запись, чтение данных)
- `sel_st` -- увеличить `SP` или уменьшить
- `alu` -- сигнал АЛУ выполнить сложение или вычитание


## Control Unit
  ![alt text](scheme/control-unit.svg "DataPath")
Регистры:
- `IP` -- стековые регистры  
- `SC` -- step counter хранит номер такта
`SC` необходим для многотактовых инструкций, в реализации отсутствует, т.к. неявно задан потоком управления.
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

``` asm
push 72
push 0
ld
pop
pop
push 101
push 32
ld
pop
pop
push 108
push 64
ld
pop
pop
push 108
push 96
ld
pop
pop
push 111
push 128
ld
pop
pop
push 44
push 160
ld
pop
pop
push 32
push 192
ld
pop
pop
push 119
push 224
ld
pop
pop
push 111
push 256
ld
pop
pop
push 114
push 288
ld
pop
pop
push 108
push 320
ld
pop
pop
push 100
push 352
ld
pop
pop
push 33
push 384
ld
pop
pop
push 0
push 416
ld
pop
pop
push 0
push 448
ld
pop
pop
push 448
mov
mov
outc
push 448
mov
push 32
add
push 448
ld
pop
pop
jz 2848
jump 2400

```

Журнал для программы Hello_world(не весь):

``` python
PS E:\projects\stack_vm> python translate.py examples/hello_world.lisp bin
PS E:\projects\stack_vm> python machine.py bin examples/inp
DEBUG:root:started emeulation
DEBUG:root:TICK:   0 IP:     0 TOS:         0 STACK[SP]:         0 STACK[SP-1]:         0 SP:   0 INSTR: push  ARG:        72
DEBUG:root:TICK:   2 IP:    32 TOS:        72 STACK[SP]:        72 STACK[SP-1]:         0 SP:   1 INSTR: push  ARG:         0    
DEBUG:root:TICK:   4 IP:    64 TOS:         0 STACK[SP]:         0 STACK[SP-1]:        72 SP:   2 INSTR: ld    ARG:         0    
DEBUG:root:TICK:   5 IP:    96 TOS:         0 STACK[SP]:         0 STACK[SP-1]:        72 SP:   2 INSTR: pop   ARG:         0    
DEBUG:root:TICK:   7 IP:   128 TOS:        72 STACK[SP]:        72 STACK[SP-1]:         0 SP:   1 INSTR: pop   ARG:         0    
DEBUG:root:TICK:   9 IP:   160 TOS:         0 STACK[SP]:         0 STACK[SP-1]:         0 SP:   0 INSTR: push  ARG:       101    
DEBUG:root:TICK:  11 IP:   192 TOS:       101 STACK[SP]:       101 STACK[SP-1]:         0 SP:   1 INSTR: push  ARG:        32    
DEBUG:root:TICK:  13 IP:   224 TOS:        32 STACK[SP]:        32 STACK[SP-1]:       101 SP:   2 INSTR: ld    ARG:         0    
DEBUG:root:TICK:  14 IP:   256 TOS:        32 STACK[SP]:        32 STACK[SP-1]:       101 SP:   2 INSTR: pop   ARG:         0    
DEBUG:root:TICK:  16 IP:   288 TOS:       101 STACK[SP]:       101 STACK[SP-1]:         0 SP:   1 INSTR: pop   ARG:         0    
DEBUG:root:TICK:  18 IP:   320 TOS:         0 STACK[SP]:         0 STACK[SP-1]:         0 SP:   0 INSTR: push  ARG:       108    
DEBUG:root:TICK:  20 IP:   352 TOS:       108 STACK[SP]:       108 STACK[SP-1]:         0 SP:   1 INSTR: push  ARG:        64    
DEBUG:root:TICK:  22 IP:   384 TOS:        64 STACK[SP]:        64 STACK[SP-1]:       108 SP:   2 INSTR: ld    ARG:         0    
DEBUG:root:TICK:  23 IP:   416 TOS:        64 STACK[SP]:        64 STACK[SP-1]:       108 SP:   2 INSTR: pop   ARG:         0    
DEBUG:root:TICK:  25 IP:   448 TOS:       108 STACK[SP]:       108 STACK[SP-1]:         0 SP:   1 INSTR: pop   ARG:         0    
DEBUG:root:TICK:  27 IP:   480 TOS:         0 STACK[SP]:         0 STACK[SP-1]:         0 SP:   0 INSTR: push  ARG:       108    
DEBUG:root:TICK:  29 IP:   512 TOS:       108 STACK[SP]:       108 STACK[SP-1]:         0 SP:   1 INSTR: push  ARG:        96    
DEBUG:root:TICK:  31 IP:   544 TOS:        96 STACK[SP]:        96 STACK[SP-1]:       108 SP:   2 INSTR: ld    ARG:         0    
DEBUG:root:TICK:  32 IP:   576 TOS:        96 STACK[SP]:        96 STACK[SP-1]:       108 SP:   2 INSTR: pop   ARG:         0    
DEBUG:root:TICK:  34 IP:   608 TOS:       108 STACK[SP]:       108 STACK[SP-1]:         0 SP:   1 INSTR: pop   ARG:         0    
DEBUG:root:TICK:  36 IP:   640 TOS:         0 STACK[SP]:         0 STACK[SP-1]:         0 SP:   0 INSTR: push  ARG:       111    
DEBUG:root:TICK:  38 IP:   672 TOS:       111 STACK[SP]:       111 STACK[SP-1]:         0 SP:   1 INSTR: push  ARG:       128    
DEBUG:root:TICK:  40 IP:   704 TOS:       128 STACK[SP]:       128 STACK[SP-1]:       111 SP:   2 INSTR: ld    ARG:         0    
DEBUG:root:TICK:  41 IP:   736 TOS:       128 STACK[SP]:       128 STACK[SP-1]:       111 SP:   2 INSTR: pop   ARG:         0    
<===============================================================================================================================> 
DEBUG:root:TICK: 473 IP:  2624 TOS:        32 STACK[SP]:        32 STACK[SP-1]:       416 SP:   3 INSTR: add   ARG:         0    
DEBUG:root:TICK: 475 IP:  2656 TOS:       448 STACK[SP]:       448 STACK[SP-1]:         0 SP:   2 INSTR: push  ARG:       448    
DEBUG:root:TICK: 477 IP:  2688 TOS:       448 STACK[SP]:       448 STACK[SP-1]:       448 SP:   3 INSTR: ld    ARG:         0    
DEBUG:root:TICK: 478 IP:  2720 TOS:       448 STACK[SP]:       448 STACK[SP-1]:       448 SP:   3 INSTR: pop   ARG:         0    
DEBUG:root:TICK: 480 IP:  2752 TOS:       448 STACK[SP]:       448 STACK[SP-1]:         0 SP:   2 INSTR: pop   ARG:         0    
DEBUG:root:TICK: 482 IP:  2784 TOS:         0 STACK[SP]:         0 STACK[SP-1]:         0 SP:   1 INSTR: jz    ARG:      2848    
DEBUG:root:TICK: 484 IP:  2848 TOS:         0 STACK[SP]:         0 STACK[SP-1]:         0 SP:   0 INSTR: hlt   ARG:         0    
Hello, world!
```

### prob2
Посчитать сумму четных чисел Фибоначчи до 4 миллионов.  

Поймем, что каждое третье число Фибоначчи, начиная с 2 - четное и других четных нет. А также, что текущее четное число Фибоначчи можно выразить из предыдущих по формуле: $F_n = F_{n-1} + F_{n-2} = 2F_{n-2} + F_{n-3} = 3F_{n-3} + 2F_{n-4} = 3F_{n-3} + F_{n-5} + F_{n-4} + F_{n-6} =  4F_{n - 3} + F_{n - 6}$

Тогда посчитаем последовательность в цикле, сложим результат в переменую.


``` lisp
  (defun fib(x)
     (setq fcur 8)
     (setq fprev 2)
     (setq sum 10)
     (loop 
       (setq fnew (* fcur 4))
       (setq fnew (+ fnew fprev))
       (setq fprev fcur)
       (setq fcur fnew)
       (when (< x fnew) (break))
       (setq sum (+ sum fnew))
       )
      (sum))
  (printi (fib 4000000))
```
