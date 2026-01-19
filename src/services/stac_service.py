import geopandas as gpd
import pystac_client

BBOX = (-45.51276312, -21.43537497, -43.98822504, -20.47079601)
BAND = "NDVI"
LST = "lwir11"
QA = "qa_pixel"
QA_RADSAT = "qa_radsat"
OUTPUT_DIR = ""


def run_stac(gdf: gpd.GeoDataFrame, start_date: str, end_date: str):
	"""
	Função para processar imagens via STAC.
	"""
	service = pystac_client.Client.open("https://data.inpe.br/bdc/stac/v1/")

	item_search = service.search(
		collections=["S2-16D-2", "landsat-2"],
		bbox=BBOX,
		datetime=f"{start_date}/{end_date}",
	)

	# For now, just log the number and IDs: properties of the items found
	items = list(item_search.items())
	items.sort(key=lambda x: x.properties["datetime"])

	# TODO: Ajustar busca de imagens (landsat deve pegar de 16 dias anteriores ao datetime do Sentinel)
	if items:
		last_date = items[-1].properties["datetime"]
		print(f"Last date available: {last_date}")
		print(f"Found {len(items)} items between {start_date} and {end_date}.")
		for item in items:
			print(f"Item ID: {item.id}")
			for p in item.properties:
				print(f"  {p}: {item.properties[p]}")

	# TODO: Processar as imagens conforme necessário
