SELECT
	'{"model": "redirect.DestinationManipulation", "pk": null, "fields": {"action_type_id": ' +
	CAST([ActionTypeID] AS VARCHAR) +
	', "buid": ' +
	CAST([BUID] AS VARCHAR) +
	', "view_source": ' +
	CAST([ViewSourceID] AS VARCHAR) +
	', "action": "' +
	[Action] +
	'", "value1": "' +
	COALESCE(CAST([Value1] AS VARCHAR(4096)),'null') +
	'", "value2": "' +
	COALESCE(CAST([Value2] AS VARCHAR(4096)),'null') +
	'"}},' AS JSON
FROM [dbextras].[dbo].[Destination_Manipulations]
