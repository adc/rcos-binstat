main()
{
	int sz, i;
	int *buf;
	sz = atoi(argv[1]);

	buf = malloc(sz * sizeof(int));

	for(i = 0; i < sz; i++)
	{
		scanf("%d\n", &buf[i]);
	}	
}
