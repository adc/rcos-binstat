
main(int argc, char *argv[])
{
	int sz;
	char buf[100];
	sz = atoi(argv[1]);

	if(sz < 100)
	{
		memcpy(buf, argv[2], sz);
	}

}
