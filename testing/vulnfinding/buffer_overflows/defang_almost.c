
void fixup(char *x)
{
	int i;
	char *new;
	char *old;

	new = malloc(strlen(x)*3);
	old = x;

	while(*old)
	{
		if(*old == '<'){
			*new++ = '&';
			*new++ = 'l';
			*new++ = 't';
			*new++ = ';';
		}
		else 
		if(*old == '>'){
			*new++ = '&';
			*new++ = 'g';
			*new++ = 't';
			*new++ = ';';
		} else {
			*new++ = *old;
		}

		old++;
	}

		
}

main()
{
	char buf[256];

	fgets(buf, sizeof(buf), stdin);
	fixup(buf);
}
