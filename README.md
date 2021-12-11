# Makeup

Generate[^1] pretty-printers[^2] for C structs so you can dump out their innards[^3]

[^1]: Make up 🔨
[^2]: Makeup 💄
[^3]: Makeup 🧱

## Why?

Sometimes you're dealing with a platform that doesn't have a nice debugger and your compiler doesn't have something like clang's \__builtin_dump_struct.

## How?

Install makeup

```
pip install git+https://github.com/birdstakes/makeup.git
```

Generate makeup

```
# Preprocess first for all but the simplest cases
gcc -E header.h | makeup - pretty.h
```

Apply makeup

```c
#include "header.h"

// There must be one file in which MAKEUP_IMPLEMENTATION has been defined
// before #including the generated header.
#define MAKEUP_IMPLEMENTATION

// Optional: override print functions

// Defaults to printf
// #define MAKEUP_PRINT my_cool_printf

// Defaults to MAKEUP_PRINT("%ld", (long)i)
#define MAKEUP_PRINT_SIGNED(i) MAKEUP_PRINT("cool signed number %ld", (long)i)

// Defaults to MAKEUP_PRINT("%lu", (unsigned long)u)
#define MAKEUP_PRINT_UNSIGNED(u) MAKEUP_PRINT("cool unsigned number %lu", (unsigned long)u)

// Defaults to MAKEUP_PRINT("%f", f)
#define MAKEUP_PRINT_FLOAT(f) MAKEUP_PRINT("cool float %f", f)

// Defaults to MAKEUP_PRINT("0x%p", p)
#define MAKEUP_PRINT_POINTER(p) MAKEUP_PRINT("cool pointer 0x%p", p)

// Defaults to if(s) { MAKEUP_PRINT("\"%s\"", s); } else { MAKEUP_PRINT("NULL"); }
#define MAKEUP_PRINT_STRING(s) MAKEUP_PRINT("cool string %s", s)

#include "pretty.h"

int main(void) {
    my_cool_type value = {0};

    printf("value = ");
    makeup_dump_my_cool_type(&value);
    printf("\n");

    return 0;
}
```
