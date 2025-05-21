void check_number(int num) {
    if (num > 0) {
        printf("%d is positive.\n", num);
    } else if (num < 0) {
        printf("%d is negative.\n", num);
    } else {
        printf("%d is zero.\n", num);
    }
}

int main() {
    check_number(10);
    check_number(-5);
    check_number(0);
    return 0;
}