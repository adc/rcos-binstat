main()
{
	unsigned int i;
	char *buf;

	scanf("%u\n", &i);
	buf = malloc(i+1);

	fgets(buf, i, stdin);
}
