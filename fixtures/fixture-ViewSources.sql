SELECT
	'{"model": "redirect.ViewSource", "pk": null, "fields": {"view_source_id": ' +
	CAST([View_Source_ID] AS VARCHAR) +
	', "name": "' +
	[Friendly_Name] +
	'", "microsite": ' +
    CAST([Landing_Pages] AS VARCHAR) +
	'}},' AS JSON
FROM [Click].[dbo].[View_Sources]
