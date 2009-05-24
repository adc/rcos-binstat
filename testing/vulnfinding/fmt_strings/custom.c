#include <stdio.h>
#include <stdarg.h>

#define MSG_SIZE 100

void baz(const char *fmt, va_list ap)
{
char msg[MSG_SIZE];

vsnprintf(msg, sizeof msg, fmt, ap);

printf("%s", msg);
}

void bar(const char *fmt, ...)
{
va_list ap;

va_start(ap, fmt);
baz(fmt, ap);

va_end(ap);
}


main(int argc, char *argv[])
{
	bar(argv[1],argv[2],argv[3]);
}
