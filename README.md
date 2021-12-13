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
gcc -E header.h | makeup - makeup.h
```

Apply makeup

```c
#include "header.h"

// Optional: override print functions
// See the top of the generated header for more

// Defaults to printf
// #define MAKEUP_PRINT my_cool_printf

// Defaults to MAKEUP_PRINT("%ld", (long)i)
#define MAKEUP_PRINT_SIGNED(i) MAKEUP_PRINT("cool signed number %ld", (long)i)

// Defaults to nothing
#define MAKEUP_PRINT_OFFSET(o) MAKEUP_PRINT("%04x ", o)

// There must be one file in which MAKEUP_IMPLEMENTATION has been defined
// before #including the generated header.
#define MAKEUP_IMPLEMENTATION
#include "makeup.h"

int main(void) {
    my_cool_type value = {0};

    printf("value = ");
    makeup_dump_my_cool_type(&value);
    printf("\n");

    return 0;
}
```
