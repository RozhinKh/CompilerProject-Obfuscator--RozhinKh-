void manipulate_string(char *str) {
    char *p = str;
    int i = 0;
    while (*(p + i) != '\0') {
        if (i % 2 == 0) {
            *(p + i) = *(p + i) + 1;
        } else {
            *(p + i) = *(p + i) - 1;
        }
        if (*(p + i) == '`') { // Boundary condition
             *(p + i) = 'z';
        }
        if (*(p + i) == '{') { // Boundary condition
             *(p + i) = 'a';
        }
        i++;
    }
}



int main() {
    char my_string[] = "HelloWorld123";
    char *ptr_to_str = my_string;

    printf("Original: %s\n", ptr_to_str);
    manipulate_string(ptr_to_str);
    printf("Manipulated: %s\n", ptr_to_str);

    // Accessing elements in reverse using pointer arithmetic
    for (int i = 0; i < strlen(ptr_to_str); ++i) {
        putchar(*(ptr_to_str + strlen(ptr_to_str) - 1 - i));
    }
    printf("\n");

    return 0;
}