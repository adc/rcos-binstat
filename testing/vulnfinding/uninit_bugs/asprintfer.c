main()
{	
	char *buf;
	int ret;
	ret = asprintf(&buf, "echo %s %d", "HI there", 33);
	if(ret == NULL)
	{
		return 1;
	}
	
	system(buf);
}
