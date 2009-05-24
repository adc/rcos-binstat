int main(int argc, char *argv[])
{
	unsigned short a;
	unsigned short b;
	int i;
	char buf[100];

	a = atoi(argv[1]);	
	b = atoi(argv[2]);	

	if(a*b > 100)
	{
		return 0;
	}

	for(i = 0; i < a*b; i++)
	{
		buf[i] = getc();
	}

	return 0;
}	
