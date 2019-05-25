# <>C lang
&lt;>C is a simple and small extension of C language.
## Precompiler

An earlier pre-compiler `CPPC` is available and written in `Python3`.

## Language
### Template structures

The first obvious think that could be integrated are template `struct`and `functions`, for example for a linked list in `C`  can be implemented like this: 

```C
typedef struct List_int {
  int value;
  struct List_int *next;
} List_int;
```
For every desired type you have to implement a `struct`.
For more generic case you could implement the list as:

```C
typedef struct List {
  void * value;
  struct List * next;
} List;
```
However there is pointer (less safe) and casting a void pointer to something else.
The template approach is more readable and safe:

```c
typedef struct List<T> {
  T value;
  struct List<T> * next;
} List<T>;
```

Then by simply calling `List<int>` the correct code will be generated during compilation time.

### Template namespace functions

Often however a series of methods or functions have to be implemented for this kind of structure. For example for such linked list 2 basic methods could be the `push` method and the `size`. It is possible to define its as:
```c
List<T> * List<T>::push(List<T> * head, T val);
size_t List<T>::size(List<T> * head);
```
The function call then is simply:
```c
List<int> * el = List<int>::push(NULL, 1);
printf("size: %d\n", List<int>::size(el));
```
Only the used functions and for the used types will be generated during compilation time.
Using this syntax is possible to define function with same name (e.g. `size`) for different structure or problem using different namespaces.

### Lambda functions

Another practical syntactic sugar is `lambda`: those permits to create in-line anonymous functions very simply :

```c
int main() {
    int (*succ)(int) = lambda (int n) => int {
        return x + 1;
    };
    return succ(0);
}
```

### Template functions

In many cases however template functions can be very useful even without any specific namespace.

```c
T convert<S,T>(S value)
{
  return (T)value;
}

(T (*)(S)) map<T, S, func>() {
   return lambda : (S value) => T {
       return func(value);
   } 
}
```

### Rewriting macros
For more generic problems it is possible to define rewriting macros with the `@NAME<VARS>{}` synthax:

```c
#include <stdio.h>
@reinclude<LIB> {
#include<LIB>
}
```
To execute the macro simply:

```c
// ...
@reinclude<math.h>;
//...
```
