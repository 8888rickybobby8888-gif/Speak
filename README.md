<p align="center"><img src="icons/speak.png" alt="Speak logo" width="128"></p>

# Speak

A programming language that reads like pseudocode. Words for structure (`if`, `repeat`, `return`), symbols for maths and comparing (`+ - * / % = < >`). No abbreviations. Write it the way you would write pseudocode on paper: [see the pseudocode style](#318-pseudocode-style).

A Speak program is turned into Python and run, so **any Python library works**, including numpy.

```
import numpy as np

ask "What is your name?" store as name
if name = "Ada" then
  print "Welcome back,", name
otherwise
  print "Nice to meet you,", name
end if

numbers = np.array([1, 2, 3])
print "Mean:", np.mean(numbers)
```

## Contents

1. [Setup and running](#1-setup-and-running)
2. [Debugging](#2-debugging)
3. [Language reference](#3-language-reference)
   - [Program shape](#31-program-shape) · [Comments](#32-comments) · [Values](#33-values) · [Variables](#34-variables-and-assignment) · [Output and input](#35-output-and-input)
   - [Operators](#36-operators) · [Conditions](#37-conditions) · [Loops](#38-loops) · [Functions](#39-functions) · [Classes](#310-classes)
   - [Text](#311-text) · [Lists](#312-lists) · [Dictionaries and tuples](#313-dictionaries-and-tuples) · [Built-in phrases](#314-built-in-phrases)
   - [Importing and Python libraries](#315-importing-and-python-libraries) · [Reserved words](#316-reserved-words-and-names) · [Speak libraries: `use`](#317-speak-libraries-use) · [Pseudocode style](#318-pseudocode-style)
4. [Quick reference](#4-quick-reference)
5. [Speak to Python translation](#5-speak-to-python-translation)
6. [Errors](#6-errors)
7. [Limits and gotchas](#7-limits-and-gotchas)
8. [Examples](#8-examples)
9. [Project layout and building](#9-project-layout-and-building)

---

## 1. Setup and running

**Requirements:** Python 3 (any recent version) and VS Code. Libraries such as numpy are installed with `pip install numpy`.

**Get the code and install it:**

```bash
git clone https://github.com/8888rickybobby8888-gif/Speak.git
cd Speak
python -m unittest discover tests        # optional: run the tests
python build.py                          # builds speak-language-<version>.vsix
code --install-extension speak-language-0.9.0.vsix --force
```

Then reload VS Code. Speak is licensed under the GNU General Public License v2 (see `LICENSE`).

### In VS Code

The extension is installed as `local.speak-language`. Open any `.speak` file and you get:

| Feature | How |
| --- | --- |
| Syntax highlighting | automatic. Definitions, calls, library calls, built-in phrases and classes each have their own colour |
| Snippets | type `if`, `ifotherwise`, `repeat`, `while`, `foreach`, `forcount`, `define`, `ask`, `class`, `classextends`, `whencreated`, `create` and press `Tab` |
| Auto-indent | indents after `then`, `otherwise`, `repeat`, `while`, `for`, `define function`, `define class`, `when ...` and dedents on `end ...` |
| Comment toggle | `Ctrl+/` adds or removes `note ` |
| Run | the play button at the top right, or `Ctrl+F5`. Runs in a terminal named "Speak" |
| Debug | the bug button, or `F5` (see [Debugging](#2-debugging)) |
| Problems panel | mistakes appear as red squiggles and in the Problems panel **as you type**, without running the program. Every mistake is listed, not just the first. See [Checking as you type](#checking-as-you-type) |
| Quick fix | on a squiggle with a `Did you mean ...?` suggestion, press `Ctrl+.` and choose `Change to ...` |

#### Checking as you type

While you type, Speak checks the whole file in the background and reports what it finds in the Problems panel, with squiggles under the lines:

- **Mistakes in how a line is written:** a misspelt command, a missing quote, an unclosed bracket, a missing `to`/`by`/`then` where one is needed, a block that is never closed.
- **Names that are never given a value anywhere in the program:** almost always a typo. Names inside text brackets, like `"(yes or no)"`, are not flagged, because those are allowed to be missing.
- **Every problem at once:** one bad line does not hide the others. A bad first line of a block does not flood you with knock-on errors.
- **Suggestions:** `Did you mean "print"?` comes with a quick fix.
- The check never runs your program. It cannot find mistakes that only appear while running (dividing by zero, an out-of-range position), and a name used before it is first assigned is only caught when the program runs.
- Turn it off with the setting `speak.checkWhileTyping`. From the terminal, `python src/speak.py --check-json < program.speak` prints the problems as JSON.

**Which Python is used:** the setting `speak.pythonPath` if set, otherwise the interpreter selected in the VS Code Python extension, otherwise `python`. Point it at a virtual environment to use libraries installed there.

**Install from this folder:**

```bash
python build.py
code --install-extension speak-language-0.9.0.vsix --force
```

Then reload VS Code (`Ctrl+Shift+P` → "Developer: Reload Window"). To try it without installing, open this folder and press `F5` using the "Try the Speak extension" configuration.

### Without VS Code

```bash
python src/speak.py examples/tour.speak
```

Exit code is `0` on success and `1` if Speak reports a problem.

---

## 2. Debugging

Click the bug button at the top right of a `.speak` file, or press `F5`. No `launch.json` is needed.

| Action | How |
| --- | --- |
| Breakpoint | click left of a line number. A breakpoint on a blank or comment line moves to the next statement |
| Continue | `F5` |
| Step over | `F10` |
| Step into | `F11` |
| Step out | `Shift+F11` |
| Call stack | shown while paused; click a frame to see its variables |
| Variables | lists, dictionaries and objects expand |
| Watch, hover, Debug Console | any Speak expression works, for example `total * 2` or `item 1 of fruits` or `pet.energy` |
| Error stop | if the program fails, the debugger stops on the failing line so you can look around |
| Input | the program runs in a VS Code terminal, so `ask` works while debugging |

### Launch configuration (optional)

```json
{
  "name": "Debug current Speak file",
  "type": "speak",
  "request": "launch",
  "program": "${file}",
  "stopOnEntry": false
}
```

| Property | Meaning | Default |
| --- | --- | --- |
| `program` | the `.speak` file to run | `${file}` |
| `stopOnEntry` | pause on the first line | `false` |
| `cwd` | folder to run in | the program's folder |

"Run Without Debugging" is supported and ignores breakpoints.

**Limits:** breakpoints only work in the file being run (not in imported files). There is no Pause button for a running program, and variable values cannot be edited from the Variables panel.

---

## 3. Language reference

### 3.1 Program shape

- One statement per line. There are no semicolons and no line continuations.
- Blocks open with a keyword line and close with `end ...` (see the next point for when you may leave it out):

  | Block | Opens | Closes |
  | --- | --- | --- |
  | decision | `if ... then` | `end if` |
  | repeat | `repeat N times` | `end repeat` |
  | repeat until | `repeat` | `until condition` |
  | while | `while condition` | `end while` |
  | for | `for ...` | `end for` or `next` |
  | function | `define function name` or `function name` | `end function` |
  | procedure | `procedure name` | `end procedure` |
  | class | `define class Name` | `end class` |
  | constructor / text form | `when created ...` / `when shown as text` | `end when` |

- Every `end X` can be written as one word: `endif`, `endwhile`, `endfor`, `endrepeat`, `endfunction`, `endprocedure`, `endclass`, `endwhen`.
- **The `end ...` lines are optional when the block's body is indented.** A block whose body is indented ends at the first later line that is indented no more than the line that opened it, or at the end of the file. These two programs are identical:

  ```
  if answer = 20 then            if answer = 20 then
    print "correct"                print "correct"
  otherwise                      otherwise
    print "incorrect"              print "incorrect"
  print "done"                   end if
                                 print "done"
  ```

  If the body is **not** indented, `if` still needs no `end if`: with no `end if` anywhere to close it, an `if` takes just the **next line** as its body (see Conditions). Every other block (`while`, `for`, `repeat`, `function`, `class`) needs its `end ...` line when its body is not indented, because Speak cannot tell where it stops. Mixing is fine: use `end ...` wherever you like for clarity. Indent with spaces or tabs (a tab counts as four spaces) and keep a block's lines lined up.
- **Keywords can be written in any case:** `if`, `If` and `IF` are the same, as are `END IF` and `endif`. Names are case sensitive (`Total` and `total` are different) and text is never changed.
- Names use letters, digits and `_`, and cannot start with a digit.

### 3.2 Comments

```
note This whole line is a comment.
# This is a comment too.
total = 5   # and this one ends the line
```

A comment is a line whose first word is `note`, or anything after a `#` (outside quotes). So `#` can also finish a line of code. Blank lines are ignored.

### 3.3 Values

| Kind | Examples | Notes |
| --- | --- | --- |
| Whole number | `0`, `42` | |
| Decimal number | `3.14`, `1e3`, `2.5e-4` | write `0.5`, not `.5`. A negative number is `-5` (an operator applied to `5`) |
| Text | `"hello"` | double quotes only. Escapes: `\n` new line, `\t` tab, `\"` quote, `\\` backslash |
| True or false | `true`, `false` | |
| Nothing | `nothing` | the empty value (Python `None`) |
| List | `a list of 1, 2, 3`, `[1, 2, 3]`, `an empty list` | see [Lists](#312-lists) |
| Dictionary | `{"name": "Ada"}` | see [Dictionaries and tuples](#313-dictionaries-and-tuples) |
| Tuple | `(1, 2)` | |

How values print: `true`, `false`, `nothing`; a decimal that is a whole number prints without `.0` (`10 / 2` prints `5`); lists print as `[1, "two", 3]`. Dictionaries and other Python or numpy objects print the way Python prints them.

### 3.4 Variables and assignment

```
age = 30                     note create or change a variable
low, high = 1, 9             note several at once
age += 1                     note same as age = age + 1
age -= 1
age *= 2
age /= 2
pet.name = "Rex"             note change a property
numbers[0] = 99              note change a list item (counting from 0)
item 2 of numbers = 99       note change a list item (counting from 1)
item 2 of numbers += 1

total <- 0                   note arrow form, as on paper (also written with the ← character)
set total to 0               note "set ... to" form
increase total by 5          note same as total += 5 (by 1 if you leave "by" out)
decrease total by 2
add 3 to total               note same as total += 3 (a list gets the item added instead)
subtract 2 from total        note same as total -= 2
multiply total by 4          note same as total *= 4
divide total by 2            note same as total /= 2
swap first and second        note exchange two values
let total be 10              note same as total = 10
```

- A variable exists from its first assignment. Using a name before that gives an error.
- `+=` works on text and lists too (`name += "!"`).
- `=`, `<-`, `set ... to` and `let ... be` all assign. `=` at the start of a line assigns. Inside a condition, `=` compares. `flag = a = b` stores whether `a` equals `b`.

### 3.5 Output and input

**Print:**

```
print "Total:", total        note values are separated by one space
print("Total:", total)       note Python style also works
print                        note a blank line
output "Total:", total       note "output" and "display" mean exactly the same as "print"
display "Total:", total
```

If a line is `print (a, b)` with brackets around the whole thing, it is treated as Python style and prints `a b`.

**Values inside text.** In `print`, `output`, `display` and the question of `ask` or `input`, anything in brackets inside the text is replaced by its value:

```
name = "Ada"
score = 41
print "hello (name)"                         note hello Ada
print "hello (name), next is (score + 1)"    note hello Ada, next is 42
ask "How old are you, (name)?" store as age
print "Items: (length of items), first: (item 1 of items)"
```

- The brackets can hold a name, a property (`(pet.name)`), a calculation (`(score + 1)`), a call (`(double(4))`), `item 1 of ...`, `length of ...` and so on: any Speak expression.
- Brackets that are **not** values are left alone, so ordinary text still works: `"(yes or no)"`, `"(see below)"`, `"smile :("`. Brackets holding only numbers or symbols, such as `"Press (1) to start"` or `"(2 + 3)"`, are also left alone, and so is a bracket naming something that does not exist.
- To keep a bracket that would be filled in, write `\(`: `print "type \(name) to see it"` prints `type (name) to see it`.
- This applies to text typed directly in those statements. Text stored first (`s = "hello (name)"`) is not filled in. Use `+` for that: `s = "hello " + name`.
- An error inside the brackets (such as dividing by zero) is reported on that line.

**Input:**

```
ask "What is your name?" store as name
input name                   note no question, just waits for an answer
input "Your name?" store as name
```

If the reply looks like a number (`20`, `-3`, `2.5`) it is stored as a number, so you can compare and calculate with it straight away. Anything else is stored as text.

```
ask "What is 10 + 10?" store as answer
if answer = 20 then
  print "correct"
else
  print "incorrect"
end if
```

To keep a numeric-looking reply as text (a phone number, a postcode with leading zeros), turn it back with `text version of answer`. Note that `007` becomes the number `7`.

### 3.6 Operators

| Operator | Meaning | Example |
| --- | --- | --- |
| `+` | add numbers, join text, join lists. Text plus a number joins them as text | `"Hi " + name`, `"Score: " + score` |
| `-` | subtract, or negate | `total - 1`, `-x` |
| `*` | multiply (also repeats text or lists) | `3 * 4` |
| `/` | divide (always gives a decimal) | `7 / 2` is `3.5` |
| `%` | remainder | `7 % 4` is `3` |
| `**` | power | `2 ** 3` is `8` |
| `@` | matrix multiply (numpy) | `a @ b` |
| `=` | equal | `x = 5` |
| `!=` | not equal | `x != 5` |
| `<` `>` `<=` `>=` | less, greater, at most, at least | `x >= 5` |
| `contains` | list holds a value, or text holds text | `names contains "Ada"`, `"abc" contains "b"` |
| `and` `or` `not` | logic | `x > 1 and not done` |
| `( )` | grouping | `(1 + 2) * 3` |

**Order of work, tightest first:**

1. brackets, then calls, `.property` and `[index]`
2. `**` (and a leading `-`)
3. `*` `/` `%` `@`
4. `+` `-`
5. `=` `!=` `<` `>` `<=` `>=` `contains` (one comparison per expression, so `a < b < c` is not allowed. Use `a < b and b < c`)
6. `not`
7. `and`
8. `or`

`-2 ** 2` is `-4`. `2 ** 3 ** 2` is `512` (right to left).

**Operators in words.** Every symbol above can also be written as words, and the two styles mix freely:

| Words | Symbol |
| --- | --- |
| `plus`, `minus` | `+`, `-` |
| `times`, `multiplied by` | `*` |
| `divided by` | `/` |
| `modulo` | `%` |
| `to the power of` | `**` |
| `is equal to`, `is`, `equals` | `=` |
| `is not equal to`, `is not` | `!=` |
| `is greater than`, `is less than` | `>`, `<` |
| `is at least`, `is greater than or equal to` | `>=` |
| `is at most`, `is less than or equal to` | `<=` |
| `does not contain` | the opposite of `contains` |

```
if low is less than 5 and high is at least 10 then
  set total to low plus high times 2
end if
```

`times` is only maths when a value follows it, so `repeat 3 times` still works. `3 times 4` is `12`.

**Other ways to write the same operators**, for people used to pseudocode:

| Write | Same as | Note |
| --- | --- | --- |
| `<>`, `≠` | `!=` | not equal |
| `==` | `=` | equal |
| `≤`, `≥` | `<=`, `>=` | |
| `×`, `÷` | `*`, `/` | |
| `//` | whole-number division | `7 // 2` is `3`, `-7 // 2` is `-4`. Same level as `*` |
| `<-`, `←` | `=` | assignment, not a comparison. `<-` is an arrow only when it has spaces on both sides, so `x <-5` still means `x < -5` |

**Joining text and numbers.** When one side of `+` is text, the other side is turned into text automatically, so you can write what you would on paper:

```
total = 78.5
print "Total: " + total                 note Total: 78.5
message = "You scored "
message += total                        note += works the same way
add 1 to message                        note and "add ... to" too
print "Average: " + (a + b) / 2         note use brackets so the sum happens first
```

This works for numbers, `true` and `false`, `nothing` and lists (`"l: " + [1, 2]` gives `l: [1, 2]`). Whole decimals lose the `.0`, so `"x" + 10 / 2` is `x5`. Two numbers still add (`1 + 2` is `3`), two pieces of text still join, and `-`, `*` and `/` are never changed: `"a" - 1` is an error. `text version of` is still there when you want an explicit conversion, for example `text version of (3 + 4)`.

### 3.6a Conditions use Python truthiness

A condition does not have to be `true` or `false`. These count as false: `false`, `nothing`, `0`, `0.0`, empty text, empty list, empty dictionary. Everything else counts as true. (With numpy arrays of more than one item, `and`/`or`/`if` raise an error. Reduce first with `np.any(...)` or `np.all(...)`.)

### 3.7 Conditions

```
if score >= 90 then
  print "A"
otherwise if score >= 80 then
  print "B"
otherwise
  print "Keep going"
end if
```

- `otherwise if ... then` can repeat any number of times.
- `otherwise` (the final fallback) is optional.
- `else` and `else if` are accepted as alternative spellings of `otherwise` and `otherwise if`.
- `then` is optional: `if score >= 90` on its own line is fine.

**`then` and `end if` are both optional.** All of these work:

```
if score >= 90 then print "A"                       note one line
if score >= 90 print "A"                            note one line, no then
if score >= 90 then print "A" else print "B"        note one line with an else
if score >= 90 then print "A"
else if score >= 80 then print "B"                  note one-line branches on separate lines
else print "C"

if score >= 90
  print "A"                                         note indented body: no end if needed
else
  print "B"

if score >= 90
print "A"                                           note not indented, no end if: the next line is the body
else
print "B"
print "this line is after the if"
```

How Speak decides where an `if` ends:

1. **Body on the same line:** the rest of the line is the body. A matching `else` can be on the same line, or on the next line lined up with the `if` (or further in).
2. **Indented body:** the block ends at the first line that is no longer indented, or at the end of the file.
3. **Not indented, with an `end if` further on:** the block runs to that `end if`, as always.
4. **Not indented, with no `end if` to close it:** the body is only the next statement. So `if x > 3` followed by two unindented lines runs only the first of them when the condition is true. Add `end if`, or indent, if you want more than one line.

The same applies to `else if` and `else` branches. Blocks other than `if` (`while`, `for`, `repeat`, functions, classes) still need an `end ...` line or an indented body.
- There is one `end if` for the whole chain, and it is optional (see below).

### 3.8 Loops

```
repeat 3 times                      note count can be any expression
  print "hello"
end repeat

while countdown > 0
  countdown -= 1
end while

for number from 1 to 5              note includes both ends: 1 2 3 4 5
  print number
end for

for number from 10 to 0 by -5       note steps: 10 5 0
  print number
end for

for each fruit in fruits            note lists, text, dictionaries (keys), numpy arrays
  print fruit
end for

repeat                              note runs the body, THEN checks: always runs at least once
  ask "Password?" store as attempt
until attempt = "open"
```

- `do` is optional at the end of `while`, `for`, `for each` and `repeat N times` lines: `while x < 5 do`.
- A `for` loop can close with `next` or `next number` instead of `end for`.
- `repeat ... until condition` stops when the condition becomes true. `stop looping` and `skip to next round` work inside it too (skipping still checks the `until`).
- A `repeat` with no `until` line gives `This "repeat" needs an "until" line to finish it.`

Inside any loop:

| Statement | Effect |
| --- | --- |
| `stop looping` | leave the loop |
| `skip to next round` | jump to the next round |

Notes: `from ... to ... by ...` allows decimals and negative steps; `by 0` is an error. `for number from 3 to 1` (counting up with the end below the start) does nothing, use `by -1`.

### 3.9 Functions

```
define function greet with person, greeting
  return greeting + ", " + person + "!"
end function

function average(numbers)             note "function" without "define", values in brackets
  return sum(numbers) / length of numbers
endfunction

procedure shout(message)               note same as a function that returns nothing in particular
  print uppercase of message
endprocedure

print greet("Ada", "Hello")            note Python style call
print call greet with "Ada", "Hello"   note Speak style call
call greet with "Ada", "Hello"         note as a statement, result ignored
greet("Ada", "Hello")                  note also fine as a statement
```

- `define function name`, `function name` and `procedure name` all define a function. Its values come after `with` (`with a, b`) or in brackets (`(a, b)`). With neither, it takes no values.
- `return value` hands a value back; `return a, b` hands back a tuple (unpack with `x, y = pair(1, 2)`); `return` on its own ends the function early and gives back `nothing`.
- A function with no `return` gives back `nothing`.
- Functions can call themselves (recursion) and be defined inside other functions.
- **Functions and classes can be defined anywhere in the file**, above or below the line that uses them. Speak moves `import`/`use` lines and then definitions to the front before running. Only definitions at the top level move (not ones inside another function, class or `if`). One consequence: a class body that runs code which needs a variable set earlier in the file (for example `count = start` directly inside a class) should be avoided.
- **Functions can change variables from outside**, as pseudocode does. See [Variables inside functions](#variables-inside-functions) below.
- Keyword values work for library functions: `np.linspace(0, 1, num=5)`. Inside `( )` or after `call ... with`, `name = value` means a keyword value.
- `call name with ...` takes all the comma-separated values to the end of the line (or up to a closing bracket). In a list of values, write `print call add with 1, 2` rather than putting more values after it.

#### Variables inside functions

```
total <- 0
count <- 0

procedure add_one()
  total <- total + 1         note changes the total from outside
  increase count             note so does this
endprocedure

add_one()
add_one()
print total, count           note 2 2
```

The rules:

- **A name that the main program also uses is shared.** If the main program (outside any function) gives a name a value anywhere, then assigning to that name inside a function changes the outside variable instead of making a new one. This applies to `=`, `<-`, `set`, `let`, `+=`, `increase`, `add`, `swap`, `ask ... store as` and the like.
- **A function's values (parameters) are always private.** `function f(total)` has its own `total`.
- **Loop counters are always private.** `for n from 1 to 3` and `for each item in ...` inside a function never touch an outside `n` or `item`.
- **A new name made inside a function is private to it.** If the main program never assigns `y`, a function that assigns `y` has its own `y`, and `print y` outside fails with the usual "I do not know what y is".
- **A function nested inside another function can change the outer function's variables** in the same way.
- **Reading never needs a declaration.** A function can always read an outside variable.

Two statements for when you want to choose:

| Write | Meaning |
| --- | --- |
| `local total` | `total` is private to this function even though the main program has a `total`. List several: `local a, b` |
| `global total` | `total` is shared even if the main program never assigns it. This is how a function creates a variable the rest of the program can use. List several: `global a, b` |

Put them at the top of the function. Reading a `local` name before giving it a value is an error: `"x" was used inside a function before it was given a value there. Give it a value first, or write "global x" to use the one from outside.`

Things to watch: because the sharing is by name, a recursive function that assigns to a shared name changes it for every call (use `local` or a different name), and a function that happens to assign a name the main program also uses will change it. `local name` is the way to say "this one is mine".

### 3.10 Classes

```
define class Animal
  when created with name, sound
    this.name = name
    this.sound = sound
    this.energy = 10
  end when

  define function speak
    print this.name, "says", this.sound
    this.energy -= 1
  end function

  when shown as text
    return "Animal called " + this.name
  end when
end class

define class Dog extends Animal
  when created with name
    call parent with name, "woof"
    this.tricks = an empty list
  end when

  define function speak
    parent.speak()
    print "(wags tail)"
  end function
end class

pet = create Dog with "Rex"
pet.speak()
print pet                      note uses "when shown as text"
print pet.tricks, pet.energy
```

| Piece | Syntax |
| --- | --- |
| Define | `define class Name` ... `end class` |
| Inherit | `define class Child extends Parent`; several parents: `extends A, B` |
| Constructor | `when created` or `when created with a, b` ... `end when` |
| Text form | `when shown as text` ... `end when` (must `return` text) |
| Method | `define function name` or `... with a, b` inside the class |
| This object | `this` (never written as a parameter) |
| Properties | `this.name = value`, read as `this.name` or `pet.name` |
| Make one | `create Name with a, b` or `Name(a, b)` |
| Parent | `call parent with a, b` (parent's constructor), `parent.method(...)` |
| Class-wide value | a plain `name = value` directly inside the class, outside any method |

Rules: `when created` and `when shown as text` only work directly inside a class. Methods can use Python's special names too, for example `define function __add__ with other`. Class names conventionally start with a capital letter (it also colours them).

### 3.11 Text

```
greeting = "Hello, " + name           note join
loud = uppercase of greeting          note HELLO, ...
quiet = lowercase of greeting
size = length of greeting
first = item 1 of greeting            note first letter (counting from 1)
first = greeting[0]                   note first letter (counting from 0)
part = greeting[0:5]                  note letters 0 up to (not including) 5
has = greeting contains "ell"         note true
as_text = text version of 42          note "42"
as_number = number version of "42"    note 42
```

All Python text methods are available too: `greeting.replace("l", "L")`, `greeting.split(", ")`, `greeting.strip()`, `"-".join(parts)`, and so on.

### 3.12 Lists

```
fruits = a list of "apple", "banana"
fruits = ["apple", "banana"]          note same thing
empty = an empty list

add "cherry" to fruits                note append
remove item 1 from fruits             note delete by position (counting from 1)
print item 1 of fruits                note "apple" (counting from 1)
item 2 of fruits = "blueberry"        note change
print length of fruits
print fruits contains "apple"
for each fruit in fruits
  print fruit
end for
```

**Two ways to pick an item.** `item N of` counts from **1**, like plain English, and complains if the position does not exist. `[ ]` counts from **0**, like Python and numpy:

| Speak style (from 1) | Python style (from 0) |
| --- | --- |
| `item 1 of list` | `list[0]` |
| `item 2 of list = 9` | `list[1] = 9` |
| `remove item 1 from list` | `list.pop(0)` |
| | `list[-1]` last item |
| | `list[1:3]` items 1 and 2 (slice) |
| | `list[:2]`, `list[2:]`, `list[::2]` |
| | `grid[0, 1]` and `grid[:, 1]` (numpy rows and columns) |

Use `[ ]` with numpy arrays. All Python list methods work too: `fruits.sort()`, `fruits.reverse()`, `fruits.insert(0, "kiwi")`, `fruits.index("apple")`, `fruits.count("apple")`.

### 3.13 Dictionaries and tuples

```
person = {"name": "Ada", "age": 36}
print person["name"]
person["age"] = 37
person["city"] = "London"
for each key in person
  print key, person[key]
end for
print person.get("height", "unknown")
print person contains "name"            note true (checks the keys)
```

A tuple is a fixed group of values: `point = (3, 4)`, `x, y = point`. Tuples print like lists (`[3, 4]`). A one-item tuple needs a trailing comma: `(3,)`. The empty tuple `()` is not supported.

### 3.14 Built-in phrases

| Phrase | Gives | Example |
| --- | --- | --- |
| `length of X` | how many items or letters | `length of fruits` |
| `uppercase of X` | text in capitals | `uppercase of "hi"` is `HI` |
| `lowercase of X` | text in lower case | |
| `round of X` | nearest whole number | `round of 2.6` is `3` |
| `absolute value of X` | without the minus sign | `absolute value of -3` is `3` |
| `square root of X` | square root | `square root of 16` is `4` |
| `text version of X` | X as text | `text version of 5` is `"5"` |
| `number version of X` | text as a number | `number version of "42"` is `42` |
| `random number from A to B` | whole number from A to B, both included | `random number from 1 to 6` |
| `item N of X` | item N (from 1) of a list or text | `item 1 of fruits` |
| `a list of A, B, C` / `an empty list` | a new list | |
| `create Name with A, B` | a new object | |

The `X` after `of` is a single value: a name, number, text, call, `.property` or `[index]`, or something in brackets. Write `length of (a + b)` when you need more than that.

Everything else comes from Python: `abs(x)`, `max(a, b)`, `min(...)`, `sum(list)`, `sorted(list)`, `len(x)`, `range(5)`, `int("3")`, `float("2.5")`, `str(5)`, and so on are all available.

### 3.15 Importing and Python libraries

```
import numpy as np                          note use np.array(...), np.mean(...)
import math
import matplotlib.pyplot as plt
from math import sqrt, pi
from math import floor as round_down
from numpy import *                         note brings in every name

numbers = np.array([1, 2, 3, 4, 5])
print np.mean(numbers)
print numbers * 2
grid = np.arange(6).reshape(2, 3)
print grid.shape, grid[:, 1]
print call np.sum with numbers             note Speak style call works for libraries too
```

- Imports are resolved like Python: the program's own folder first (so a `helpers.py` next to your `.speak` file can be imported), then the standard library, then packages installed with `pip` for the Python Speak runs with.
- Prefer `import numpy as np` over `from numpy import *`. The `*` form replaces Python's `max`, `min`, `sum`, `abs` and `round` with numpy's versions, which behave differently and give confusing errors.
- A missing package gives: `I could not find the module "numpy". Install it with: pip install numpy`.
- Any attribute, method and index Python supports works: `a.b`, `a.b(c)`, `a[b]`, `a.b.c(d)[e]`.

### 3.16 Reserved words and names

Names are used for variables, functions, classes, parameters and loop counters.

- **Cannot start a line as a name** (they begin statements): `print`, `ask`, `add`, `remove`, `return`, `stop`, `skip`, `import`, `use`, `from`, `if`, `repeat`, `while`, `for`, `define`, `when`, `end`, `otherwise`, `else`, `note`, plus `output`, `display`, `input`, `set`, `let`, `increase`, `decrease`, `add`, `subtract`, `multiply`, `divide`, `swap`, `global`, `local`, `function`, `procedure`, `until`, `next`. Some of these can still be variable names when the line is an assignment: `output = 5`, `end <- 3` and `display += 1` work, while `otherwise = 1` does not. In the middle of a line they are ordinary names: `for n from start to end`.
- **Cannot be used as a name anywhere:** `then`, `otherwise`, `with`, `of`, `to`, `by`, `each`, `contains`, `and`, `or`, `not`, `true`, `false`, `nothing`, `call`, `create`, `parent`.
- **Python words cannot be names either:** `class`, `def`, `lambda`, `pass`, `global`, `nonlocal`, `del`, `try`, `except`, `finally`, `raise`, `yield`, `is`, `in`, `as`, `assert`, `async`, `await`, `elif`, `else`, `break`, `continue`, `return`, `import`, `from`, `while`, `for`, `if`, `with`. Speak tells you: `"lambda" is a reserved word and cannot be used as a name here.`
- Names such as `length`, `round` or `uppercase` are fine on their own. Only the phrases `length of`, `round of` and so on are special.
- `this` is an ordinary name that classes use. `item` is only special when followed by a position and `of`.

### 3.17 Speak libraries: `use`

`use` loads a **plain-English version** of a well-known Python library: no abbreviations, full-word names, and Speak's habits (angles in degrees, positions counting from 1). The full list of every function is in **[LIBRARIES.md](LIBRARIES.md)**.

```
use numpy
use micromelon as robot

scores = numpy.array([4, 8, 15, 16, 23, 42])
print numpy.standard_deviation(scores)          note np.std in Python

robot.connect_to_simulator()
robot.drive_forward_distance(30)
robot.turn_right(90)
print robot.distance_ahead()
robot.disconnect()
```

| Library | Replaces | Install |
| --- | --- | --- |
| `numpy` | `np.std`, `np.arange`, `np.linspace`, `np.argmax` ... | `pip install numpy` |
| `pandas` | `pd.DataFrame`, `read_csv`, `sort_values`, `groupby` ... | `pip install pandas` |
| `matplotlib` | `plt.plot`, `plt.bar`, `plt.xlabel`, `plt.savefig` ... | `pip install matplotlib` |
| `micromelon` | `RoverController`, `Motors.moveDistance`, `Ultrasonic.read`, `LEDs.writeAll` ... | `pip install micromelon` |
| `math` | `math.sqrt`, `math.floor`, `math.gcd` ... (angles in degrees) | built in |
| `random` | `random.randint`, `random.choice`, `random.sample` ... | built in |
| `time` | `time.sleep`, `time.perf_counter`, `datetime` ... | built in |

How `use` works:

- `use numpy` makes a name `numpy`. `use micromelon as robot` makes the name `robot` instead. `use numpy, math, random` loads several.
- **Every Speak library has `.raw`**, the original Python library, so nothing is out of reach: `numpy.raw.linalg.norm(values)`.
- **`numpy.list_functions()`** prints every function a library offers, with a description.
- **Any other installed Python library works with `use` too** (you get the ordinary library), for example `use json`.
- **The Python way still works** and can be mixed freely: `import numpy as np` next to `use micromelon`.
- Positions these libraries return count from 1 (`numpy.position_of_largest(values)`), so they work with `item N of`.

A few examples of the renaming:

| Python | Speak |
| --- | --- |
| `np.std(x)` | `numpy.standard_deviation(x)` |
| `np.arange(1, 10)` (stops before 10) | `numpy.numbers_from_to(1, 10)` (includes 10, like a Speak `for` loop) |
| `np.linspace(0, 1, 5)` | `numpy.evenly_spaced(0, 1, 5)` |
| `np.argmax(x)` (from 0) | `numpy.position_of_largest(x)` (from 1) |
| `plt.plot(x, y, label="a")` | `matplotlib.line_chart(x, y, "a")` |
| `plt.xlabel("Day")` | `matplotlib.x_label("Day")` |
| `pd.read_csv("f.csv")` | `pandas.read_table("f.csv")` |
| `df.sort_values("age", ascending=False)` | `pandas.sort_table(df, "age", true)` |
| `math.sqrt(x)` | `math.square_root(x)` |
| `random.randint(1, 6)` | `random.whole_number(1, 6)` or `random.roll_dice()` |
| `time.sleep(2)` | `time.wait(2)` |
| `Motors.moveDistance(30)` | `robot.drive_forward_distance(30)` |
| `Motors.turnDegrees(-90)` | `robot.turn_left(90)` |
| `Ultrasonic.read()` | `robot.distance_ahead()` |
| `LEDs.writeAll(COLOURS.RED)` | `robot.set_all_lights("red")` |
| `Sounds.playNote(NOTES.C4, 1)` | `robot.play_note("C4", 1)` |

**Micromelon notes.** Speeds are in cm/s (-30 to 30), distances in cm, angles in degrees. Colours are names (`"red"`, `"orange"`, ...) or `[red, green, blue]` lists. Notes are names like `"C4"`, `"F#5"`, `"Bb3"` or a frequency. Sensors are `"left"`, `"middle"`, `"right"`; axes are `"x"`, `"y"`, `"z"`. Start the Micromelon Robot Simulator and use `robot.connect_to_simulator()`, or `robot.connect_by_bluetooth(your robot number)` for a real rover. If nothing is connected, Speak says so in plain English. See [examples/micromelon_robot.speak](examples/micromelon_robot.speak) and [examples/micromelon_dance.speak](examples/micromelon_dance.speak).

### 3.18 Pseudocode style

Speak accepts the many ways pseudocode is usually written, so you can write what you would on paper. Everything below is optional and can be mixed freely with the standard forms.

| Idea | Standard | Also accepted |
| --- | --- | --- |
| Keyword case | `if`, `end if` | `IF`, `If`, `END IF`, `ENDIF` |
| Assign | `x = 5` | `x <- 5`, `x ← 5`, `set x to 5`, `let x be 5` |
| Add to a variable | `x += 1` | `increase x`, `increase x by 1`, `add 1 to x` |
| Take from a variable | `x -= 1` | `decrease x by 1`, `subtract 1 from x` |
| Multiply / divide a variable | `x *= 2`, `x /= 2` | `multiply x by 2`, `divide x by 2` |
| Swap | `a, b = b, a` | `swap a and b` |
| Compare | `x >= 5` | `x is at least 5`, `x is 5`, `x is not 5` |
| Maths | `a + b * c` | `a plus b times c` |
| Print | `print "hi"` | `output "hi"`, `display "hi"` |
| Input | `ask "Name?" store as name` | `input name`, `input "Name?" store as name` |
| Comment | `note text` or `# text` | `# text`, and `# text` at the end of a line |
| Not equal | `!=` | `<>`, `≠` |
| Equal | `=` | `==` |
| At most / at least | `<=`, `>=` | `≤`, `≥` |
| Times / divide | `*`, `/` | `×`, `÷` |
| Whole-number division | | `//` |
| Else | `otherwise` | `else` |
| Else if | `otherwise if` | `else if` |
| `then` after `if` | `if x > 3 then` | `if x > 3` |
| `if` on one line | | `if x > 3 then print "big"`, `if x > 3 print "big" else print "small"` |
| `do` after loops | `while x < 5` | `while x < 5 do` |
| End of a block | `end if` | `endif` (likewise `endwhile`, `endfor`, `endrepeat`, `endfunction`, `endprocedure`, `endclass`, `endwhen`) |
| End of a for loop | `end for` | `next`, `next i` |
| Loop that checks at the end | | `repeat` ... `until condition` |
| Function | `define function f with a, b` | `function f(a, b)`, `procedure f(a, b)` |
| Block without an end line | | indent the body (see Program shape); for `if`, even an unindented one-statement body needs no `end if` |

The same program, written three ways. All three run and give the same answer:

```
note Standard Speak
define function average with numbers
  total = 0
  for each n in numbers
    total += n
  end for
  return total / length of numbers
end function

if average([70, 80, 90]) >= 75 then
  print "Pass"
otherwise
  print "Try again"
end if
```

```
# Pseudocode style
function average(numbers)
  total <- 0
  for each n in numbers do
    increase total by n
  next n
  return total / length of numbers
endfunction

IF average([70, 80, 90]) >= 75 THEN
  OUTPUT "Pass"
ELSE
  OUTPUT "Try again"
ENDIF
```

```
note Indentation only, with no end lines at all
function average(numbers)
  total = 0
  for each n in numbers
    total += n
  return total / length of numbers

if average([70, 80, 90]) >= 75
  print "Pass"
else
  print "Try again"
```

See [examples/pseudocode.speak](examples/pseudocode.speak) for a longer program in this style.

---

## 4. Quick reference

| Idea | Speak |
| --- | --- |
| Comment | `note text` |
| Variable | `age = 30`, `age <- 30`, `set age to 30`, `low, high = 1, 9` |
| Change a value | `age += 1`, `-=`, `*=`, `/=`, `increase age by 1`, `add 1 to age`, `subtract 1 from age`, `multiply age by 2`, `divide age by 2`, `swap a and b` |
| Print | `print "Total:", total`, `output ...`, `display ...` or `print("Total:", total)` |
| Values in text | `print "Hello (name), you have (score + 1) points"` (also in `ask` questions) |
| Input | `ask "Your name?" store as name`, `input name` |
| Maths | `+`, `-`, `*`, `/`, `//`, `%`, `**`, `@`, or `plus`, `minus`, `times`, `divided by`, `modulo`, `to the power of` |
| Compare | `=`, `!=` (or `<>`), `<`, `>`, `<=`, `>=`, `contains`, or `is`, `is not`, `is greater than`, `is less than`, `is at least`, `is at most` |
| Logic | `and`, `or`, `not`, `true`, `false`, `nothing` |
| Decide | `if ... then` / `otherwise if ... then` / `otherwise` (or `else`) / `end if` (or `endif`) |
| Repeat | `repeat 5 times` ... `end repeat` |
| Repeat until | `repeat` ... `until condition` |
| While | `while condition` ... `end while` |
| Count | `for number from 1 to 10 by 2` ... `end for` (or `next`) |
| Each | `for each item in list` ... `end for` |
| Leave / skip | `stop looping`, `skip to next round` |
| Share / keep private | `global total`, `local total` inside a function |
| Function | `define function greet with name, greeting` ... `end function`; or `function greet(name, greeting)` ... `endfunction` |
| Procedure | `procedure greet(name)` ... `endprocedure` |
| Return | `return value` |
| Call | `greet("Ada")` or `call greet with "Ada"` |
| Keyword value | `np.linspace(0, 1, num=5)` |
| Class | `define class Dog extends Animal` ... `end class` |
| Constructor | `when created with name` ... `end when` |
| Text form | `when shown as text` ... `end when` |
| This / parent | `this.name`, `call parent with name`, `parent.speak()` |
| New object | `create Dog with "Rex"` or `Dog("Rex")` |
| Import | `import numpy as np`, `from math import sqrt` |
| Speak library | `use numpy`, `use micromelon as robot`, `numpy.list_functions()` |
| List | `a list of 1, 2, 3`, `[1, 2, 3]`, `an empty list` |
| Dictionary | `{"name": "Ada"}` |
| Item (from 1) | `item 1 of list`, `item 2 of list = 9`, `add 4 to list`, `remove item 1 from list` |
| Item (from 0) | `list[0]`, `list[1:3]`, `grid[:, 1]` |
| Phrases | `length of`, `uppercase of`, `lowercase of`, `round of`, `absolute value of`, `square root of`, `text version of`, `number version of`, `random number from 1 to 6` |

### Grammar summary

```
program        = { statement } ;
statement      = assignment | set | let | change | arithmetic | swap | scope | print | ask | input | add | remove | return | stop | skip
               | import | use | from | if | repeat | while | for | define | expression ;

assignment     = target { "," target } ( ( "=" | "<-" ) values | ("+=" | "-=" | "*=" | "/=") value )
               | "item" position "of" target ( "=" | "<-" | "+=" | "-=" | "*=" | "/=" ) value ;
set            = "set" target { "," target } "to" values | "set item" position "of" target "to" value ;
let            = "let" target { "," target } ( "be" | "=" ) values ;
change         = ( "increase" | "decrease" ) target [ "by" value ] ;
arithmetic     = "add" value "to" target | "subtract" value "from" target
               | ( "multiply" | "divide" ) target "by" value ;
swap           = "swap" target "and" target ;
scope          = ( "global" | "local" ) name { "," name } ;
print          = ( "print" | "output" | "display" ) [ values ] ;
ask            = "ask" text-value "store as" name ;
input          = "input" name | "input" text-value "store as" name ;
add            = "add" value "to" target ;
remove         = "remove item" position "from" target ;
return         = "return" [ values ] ;
stop           = "stop looping" ;       skip = "skip to next round" ;
import         = "import" dotted-name [ "as" name ] { "," ... } ;
use            = "use" name [ "as" name ] { "," name [ "as" name ] } ;
from           = "from" dotted-name "import" ( "*" | name [ "as" name ] { "," ... } ) ;

if             = "if" value [ "then" ] ( statement [ ( "else" | "otherwise" ) statement ] | block )
                 { ( "otherwise if" | "else if" ) value [ "then" ] ( statement | block ) }
                 [ ( "otherwise" | "else" ) ( statement | block ) ] [ "end if" | "endif" ] ;
repeat         = "repeat" value "times" [ "do" ] block "end repeat"
               | "repeat" block "until" value ;
while          = "while" value [ "do" ] block "end while" ;
for            = "for each" name "in" value [ "do" ] block ( "end for" | "next" [ name ] )
               | "for" name "from" value "to" value [ "by" value ] [ "do" ] block ( "end for" | "next" [ name ] ) ;
define         = ( "define function" | "define procedure" | "function" | "procedure" ) name
                 [ "with" name { "," name } | "(" [ name { "," name } ] ")" ] block ( "end function" | "end procedure" )
               | "define class" Name [ "extends" dotted-name { "," dotted-name } ] class-body "end class" ;
class-body     = { statement | when | define-function } ;
when           = "when created" [ "with" name { "," name } ] block "end when"
               | "when shown as text" block "end when" ;

value          = or ;
or             = and { "or" and } ;       and = not { "and" not } ;       not = [ "not" ] comparison ;
comparison     = sum [ ( "=" | "!=" | "<" | ">" | "<=" | ">=" | "contains" | "does not contain"
                 | "is" | "is not" | "equals" | "is equal to" | "is not equal to" | "is greater than"
                 | "is less than" | "is at least" | "is at most" ) sum ] ;
sum            = product { ( "+" | "-" | "plus" | "minus" ) product } ;
product        = unary { ( "*" | "/" | "//" | "%" | "@" | "times" | "multiplied by" | "divided by" | "modulo" ) unary } ;
unary          = "-" unary | postfix [ ( "**" | "to the power of" ) unary ] ;
postfix        = primary { "." name | "(" [ arguments ] ")" | "[" index "]" } ;
primary        = number | text | "true" | "false" | "nothing" | name | "(" values ")"
               | "[" [ values ] "]" | "{" [ key ":" value { "," key ":" value } ] "}"
               | "a list of" [ values ] | "an empty list"
               | "call" callee [ "with" arguments ] | "create" callee [ "with" arguments ]
               | "parent" | "item" position "of" postfix
               | ( "length" | "uppercase" | "lowercase" | "round" | "absolute value"
                 | "square root" | "text version" | "number version" ) "of" unary
               | "random number from" sum "to" sum ;
```

---

## 5. Speak to Python translation

Because Speak becomes Python, this table explains every behaviour above.

| Speak | Python |
| --- | --- |
| `x = 5`, `x <- 5`, `set x to 5` | `x = 5` (inside a function, Speak adds `global x` when the main program also assigns `x`) |
| `global x` / `local x` | tells that scope pass; the program just runs |
| `increase x by 2`, `add 2 to x` | `x += 2` (for a list, `add v to x` appends) |
| `subtract 2 from x` | `x -= 2` |
| `multiply x by 2`, `divide x by 2` | `x *= 2`, `x /= 2` |
| `swap a and b` | `a, b = b, a` |
| `x = a = b` | `x = (a == b)` |
| `a != b`, `a >= b` | `(a != b)`, `(a >= b)` |
| `a contains b` | `(b in a)` |
| `print a, b` (or `output`, `display`) | `_print(a, b)` (joins with a space, shows `true`/`false`/`nothing`) |
| `print "hi (name)"` | `_print(_fill(['hi ', ('(name)', lambda: (name))]))` (a missing name keeps the text as written) |
| `ask "q" store as x` | `x = _ask("q")` (a numeric reply becomes a number) |
| `repeat n times` | `for _round in range(n):` |
| `repeat` ... `until c` | `while _again or not (c):` (the body always runs once first) |
| `for i from a to b by s` | `for i in _count(a, b, s):` (includes `b`) |
| `for each x in y` | `for x in y:` |
| `otherwise if` / `otherwise` (or `else if` / `else`) | `elif` / `else` |
| `define function f with a` | `def f(a):` |
| inside a class | `def f(this, a):` |
| `when created with a` | `def __init__(this, a):` |
| `when shown as text` | `def __str__(this):` |
| `define class A extends B` | `class A(B):` |
| `create A with x` | `A(x)` |
| `call parent with x` | `super().__init__(x)` |
| `parent` | `super()` |
| `item n of x` | `_item(x, n)` (checks `1 <= n <= length`) |
| `x is greater than 3` | `(x > 3)` |
| `length of x` | `len(x)` |
| `uppercase of x` | `str(x).upper()` |
| `random number from a to b` | `random.randint(a, b)` |
| `import numpy as np` | `import numpy as np` |
| `use numpy` | `numpy = _use('numpy')` (loads `src/speak_libraries/speak_numpy.py`) |
| `use micromelon as robot` | `robot = _use('micromelon')` |

---

## 6. Errors

Errors are explained in plain English with the line number:

```
Speak problem in program.speak
Line 12: I do not know what "totl" is. Did you forget to give it a value first?
```

| Message | Cause |
| --- | --- |
| `I do not know what "x" is. Did you forget to give it a value first? Did you mean "y"?` | the name was never assigned (or is misspelt). A similar name is suggested when there is one |
| `I do not know how to start a line with "prnt". Did you mean "print"?` | an unknown word at the start of a line. A close match is suggested |
| `This block is never closed. Add "end if" after its last line.` | a block whose body is not indented and has no `end ...` line |
| `"end" has nothing to close here.` | an extra or mismatched `end ...` |
| `This text is missing its closing quote mark.` | an unterminated `"` |
| `I did not expect "x" here.` | something in the wrong place on the line |
| `I expected "to" here but found "x".` | a missing word in a fixed phrase |
| `I cannot divide by zero.` | `/` or `%` by `0` |
| `Position 9 does not exist. The length is 2, and positions start at 1.` | `item N of` out of range |
| `That position does not exist in the list. Square brackets [ ] start at 0; "item N of" starts at 1.` | `[ ]` out of range |
| `can only concatenate str (not "...") to str. Use "text version of" ...` | joining text with something that is not a number, list or `nothing` (for example an object): convert it first |
| `I could not find the module "numpy". Install it with: pip install numpy` | missing library |
| `I do not know a library called "x". Speak has its own versions of: ...` | `use` with a name that is neither a Speak library nor an installed Python library |
| `I could not connect to the rover at 127.0.0.1:9000. Is the Micromelon Robot Simulator running...` | the rover or simulator is not reachable |
| `I am not connected to a robot yet. Use connect_to_simulator() ...` | a rover command before connecting |
| `"x" was used inside a function before it was given a value there ...` | changing an outside variable with `=` in a function |
| `A function called itself too many times.` | endless recursion |
| `I could not understand this line.` | a line that is grammatical in Speak but not valid once translated, for example assigning to a number |
| `I cannot compare a number with text using "<". One of them is text. If it came from "ask" ...` | comparing a number with text (`<`, `>`, `<=`, `>=`). Often an `ask` reply that was not a number. Turn text into a number with `number version of` |
| `... "high" holds the text "yes" that "ask" stored on line 6. ...` | added to the comparison and maths messages when a variable on the failing line is text that `ask` stored. Typical cause: `ask ... store as high` overwrote a number you still needed. Store the reply in a new variable |
| `I cannot use "-" with text and a number.` | `-`, `*`, `/` and the like with the wrong kinds of value |
| `"f" needs 1 value but was given 2.` | a function called with the wrong number of values |
| `"f" is missing a value for "b".` | a function called with too few values |
| `A Dog has no "colour".` | reading a property that an object does not have |
| `The library "math" has no "square_rot". Did you mean "square_root"?` | a library function that does not exist. Similar names are suggested. For Speak libraries, `NAME.list_functions()` shows what is there |
| `The dictionary has no key "b".` | reading a dictionary key that is not there |
| `A number cannot be used like a function.` / `... looped over.` | calling or looping over the wrong kind of value |
| `ValueError: ...`, `TypeError: ...` and similar | any other Python error is shown with its Python name |

---

## 7. Limits and gotchas

- **Two ways to count list positions:** `item N of` is from 1, `[ ]` is from 0. Pick one per list and stay with it.
- **Shared by name:** a function that assigns a name the main program also assigns changes the outside variable. Use `local name` when you want a private one.
- **No chained comparisons:** `a < b < c` is not allowed.
- **No empty tuple** `()`, no `lambda`, no `try`/`except`, no `with ... as` blocks, no `del` (use `remove item`), no decorators, no generators (`yield`), no f-strings or single-quoted text.
- **An unindented `if` with no `end if` takes only the next line.** If you meant several lines, indent them or add `end if`.
- **Indentation can close blocks:** a line indented no more than a block's opener ends that block, so a body line that is accidentally dedented ends the block early (and a later `end ...` line then reports "has nothing to close").
- **No multi-line statements.** Long lists must stay on one line. (End-of-line comments with `#` are fine.)
- **`print (a, b)`** with brackets around everything prints `a b`, not a tuple.
- **`ask` converts numbers:** `007` is stored as `7`. Use `text version of` if you need the original digits.
- **Names starting with `_`** are used internally by Speak (`_print`, `_item`, ...). Avoid them.
- **Library packages are separate installs:** `use numpy` needs `pip install numpy`, `use pandas` needs `pandas`, and so on. Speak tells you the command when one is missing.
- **`from numpy import *`** replaces `max`, `min`, `sum`, `abs` and `round`. Use `import numpy as np`.
- **Loop variables stay set** after a loop ends, as in Python.
- **Recursion** is limited to about 1000 calls deep (Python's limit).
- **Debugger:** breakpoints only in the file being run; no pause button; no editing variable values.

---

## 8. Examples

| File | Shows |
| --- | --- |
| [examples/tour.speak](examples/tour.speak) | the whole core language |
| [examples/classes.speak](examples/classes.speak) | classes, `extends`, `parent`, `when shown as text` |
| [examples/numpy.speak](examples/numpy.speak) | numpy arrays, slicing, keyword values (needs `pip install numpy`) |
| [examples/fizzbuzz.speak](examples/fizzbuzz.speak) | loops and decisions |
| [examples/greeting.speak](examples/greeting.speak) | input with `ask` |
| [examples/pseudocode.speak](examples/pseudocode.speak) | a program written in pseudocode style |
| [examples/words.speak](examples/words.speak) | commands and comparisons written in words |
| [examples/text_with_values.speak](examples/text_with_values.speak) | values inside text with `(name)` |
| [examples/libraries.speak](examples/libraries.speak) | the Speak numpy, math, random and time libraries |
| [examples/charts.speak](examples/charts.speak) | drawing and saving a chart with the Speak matplotlib library |
| [examples/micromelon_robot.speak](examples/micromelon_robot.speak) | an obstacle-avoiding Micromelon rover |
| [examples/micromelon_dance.speak](examples/micromelon_dance.speak) | lights, notes and spinning on a Micromelon rover |

A small complete program:

```
note Guess the number
secret = random number from 1 to 10
guesses = 0
found = false

while not found
  ask "Guess a number from 1 to 10:" store as reply
  guess = number version of reply
  guesses += 1
  if guess = secret then
    found = true
  otherwise if guess < secret then
    print "Too low"
  otherwise
    print "Too high"
  end if
end while

print "You got it in", guesses, "guesses!"
```

---

## 9. Project layout and building

| Path | Purpose |
| --- | --- |
| `src/speak.py` | the compiler (Speak to Python) and runner |
| `src/speak_libraries/` | the Speak versions of numpy, pandas, matplotlib, micromelon, math, random and time (`speak_<name>.py`, loaded by `use`) |
| `LIBRARIES.md` | every library function, generated by `make_library_docs.py` |
| `tests/` | automated tests: `python -m unittest discover tests` |
| `src/debug_adapter.py` | the VS Code debug adapter (talks the Debug Adapter Protocol) |
| `src/speak_debug.py` | runs a program under the debugger, in a terminal |
| `extension.js`, `package.json` | the VS Code extension (run and debug commands, colours, settings) |
| `syntaxes/speak.tmLanguage.json` | highlighting rules |
| `snippets/speak.json` | snippets |
| `language-configuration.json` | comment toggling, brackets, auto-indent |
| `examples/` | sample programs |
| `build.py` | builds `speak-language-<version>.vsix` |
| `icons/` | the logo: `speak.png` (extension icon) and `speak-file.svg` (icon for `.speak` files) |
| `make_library_docs.py` | regenerates `LIBRARIES.md` from the library files |
| `make_logo.py` | redraws the logo (needs `pip install pillow`) |
| `.vscode/launch.json` | debug and extension-development launch configurations |

**Settings:**

- `speak.pythonPath`: the Python to run, check and debug with. Leave empty to use the Python extension's interpreter, or `python`.
- `speak.checkWhileTyping` (default on): check files as you type and show mistakes in the Problems panel.

**Rebuild and reinstall after any change:**

```bash
python build.py
code --install-extension speak-language-0.9.0.vsix --force
```

(Raise `version` in `package.json` first if VS Code does not pick up the update.)
