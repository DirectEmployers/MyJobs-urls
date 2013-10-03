SELECT
	'{"model": "redirect.RedirectAction", "pk": null, "fields": {"buid": ' +
	CAST([BUID] AS VARCHAR) +
	', "view_source": ' +
	CAST([ViewSourceID] AS VARCHAR) +
	', "action": "' +
	[Action] +
	'"}},' AS JSON
FROM [dbextras].[dbo].[Destination_Manipulations]
