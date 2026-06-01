# Лабораторная работа №4

Вариант: `alg | acc | neum | hw | tick | binary | trap | port | pstr | prob1 | cache`

---

## Язык программирования `Alg`

### Синтаксис языка
```
<program> ::= <decl> | <decl> <program>

<decl> ::= <var_decl> | <func_decl> | <ifunc_decl> | <statement>

<var_decl> ::= "var" <identifier> ";"
               | "var" <identifier> "=" <expression> ";"

<func_decl> ::= "func" <identifier> "(" [ <parametr_list> ] ")" <block>
<parametr_list> ::= <identifier> | <identifier> "," <parametr_list>
<ifunc_decl> ::= "ifunc" "(" <number> ")" <block>

<block> ::= "{" <statement_sequence> "}"
<statement_sequence> ::= <statement> | <statement> <statement_sequence>
<statement> ::= <var_decl>
                | <assignment>
                | <if_statement>
                | <while_statement>
                | <return_statement>
                | <func_call> ";"

<assignment> ::= <identifier> "=" <expression> ";"

<if_statement> ::= "if" "(" <condition> ")" <block>
                   [ "else" <block> ]

<while_statement> ::= "while" "(" <condition> ")" <block>

<return_statement> ::= "return" [ <expression> ] ";"

<func_call> ::= <identifier> "(" [ <argument_list> ] ")"
<argument_list> ::= <expression> | <expression> "," <argument_list>

<condition> ::= <expression> <bool_op> <expression>
<bool_op> ::= "=="
              | "!="
              | "<"
              | "<="
              | ">"
              | ">="

<expression> ::= <term>
               | <expression> "+" <term>
               | <expression> "-" <term>
               | <string>

<term> ::= <factor>
           | <term> "*" <factor>

<factor> ::= <number>
             | <identifier>
             | "(" <expression> ")"
             | <func_call>
           
<identifier> ::= <letter>
                 | <identifier> <letter>
                 | <identifier> <digit>
                 | <identifier> "_"

<number> ::= <digit>
             | <number> <digit>

<letter> ::= "a" | ... | "z"
             | "A" | ... | "Z"

<digit> ::= "0" | ... | "9"

<string> ::= "\"" [ <string_content> ] "\"" 

<string_content> ::= <sym> | <string_content> <sym>

<sym> ::= "letter" | "digit" | " " | ...
```

### Семантика

Область видимости переменных - локальная

Переменные могут иметь два типа данных:
  - int32 - целые 32-битные числа
  - string - строки, реализованы с помощью ссылок на PSTR-объект

`return` внутри функции-прерывания транслируется в `IRET`

---

## Организация памяти

---

## Система команд

---

## Транслятор 

---

## Модель процессора

---

## Тестирование