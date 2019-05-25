#include <stdio.h>
#include <stdlib.h>

@macro<LIB>{
#include <LIB>
}

T sum<T>(T a, T b); // template sum...

typedef struct List<T> {
    T value;
    struct List<T> * next;
} List<T>;

List<T> * List<T>::new(T val);

/*
main function
*/
int main(int argc, char * argv[]) {
    @macro<math.h>;
    List<int> * el = List<int>::new(1);
    int (*succ)(int) = lambda (int x) => int {
        return x + 1;
    };
    printf("%d\n",succ(sum<int>(0, 1)));
    return 0;
}


T sum<T>(T a, T b) {
    return a + b;
}


List<T> * List<T>::new(T val)
{
    List<T> * el = (List<T>*)malloc(sizeof(List<T>));
    el->value = val;
    return el;
}
