#include <stdio.h>


void yes(char *arg1)
{
	char buf[256];
	printf(arg1);
	gets(buf);
	printf(buf);
	
}

void no(char *arg1)
{
	char buf[256];
	
	(volatile)printf("false positives\n");
	sprintf(buf, "%s %d",1);

	printf(buf, arg1);
}

void paths(int number, char *buf)
{
	char b[256];

	if(number < 0)
	{
		sprintf(b, "%s");	
	} else if(number == 10)
	{	
		sprintf(b, buf);
	} else {
		sprintf(b, "HI there\n");
	}

	printf(b, buf);
	
}

int main(int argc, char *argv[])
{
	yes(argv[1]);
	no();
	paths(argc, );
}
