import logging
import time
from datetime import timedelta
from os import getenv as env

import geopandas as gpd
from pymongo import MongoClient
from shapely.geometry import MultiPolygon, Polygon
from wtss import WTSS

from src.repos.coffee_repo import update_points_time_series

logger = logging.getLogger(__name__)


def run_wtss(
	gdf: gpd.GeoDataFrame,
	start_date: str,
	end_date: str,
):
	# Mongo DB connection
	client = MongoClient(env("DB_URL", "mongodb://mongo:27017/"))
	db = client[env("DB_NAME", "campo_vertentes")]

	# WTSS service connection
	service = WTSS(env("WTSS_URL", "https://data.inpe.br/bdc/wtss/v4/"))
	coverage = service["S2-16D-2"]

	geometries = [
		geom for geom in gdf["geometry"] if isinstance(geom, (Polygon, MultiPolygon))
	]

	start_time = time.time()
	total_docs = 0
	logger.info(
		f"🕐 Iniciando processamento às {time.strftime('%H:%M:%S')}\n{start_date} até {end_date}\n"
	)

	for i, geom in enumerate(geometries):  # Retomar do polígono 984
		geocodigo = str(gdf.iloc[i]["CD_MUN"])
		logger.info(f"📍 Processando polígono {i + 1}/{len(geometries)}...")

		polygon_start_time = time.time()

		try:
			ts = coverage.ts(
				attributes=(
					"NDVI",
					"EVI",
					"B04",
					"B08",
					"B03",
				),
				geom=geom,
				start_datetime=start_date,
				end_datetime=end_date,
			)

			df = ts.df()

			if df.empty:
				logger.info("⚠️  Série temporal vazia, parando processamento.")
				break

			# Pivotar os dados
			pivoted = df.pivot_table(
				index=["geometry", "datetime"],
				columns="attribute",
				values="value",
				aggfunc="first",
			).reset_index()

			pivoted.rename(
				columns={
					"NDVI": "ndvi",
					"EVI": "evi",
					"B03": "green",
					"B04": "red",
					"B08": "nir",
					"datetime": "timestamp",
				},
				inplace=True,
			)

			# Agrupar dados por pixel (ponto)
			grouped = pivoted.groupby("geometry")
			docs = []

			for j, (pixel, group) in enumerate(grouped):
				# Criar array da série temporal
				time_series = group.drop(columns=["geometry"]).to_dict(orient="records")

				# Criar documento para MongoDB
				doc = {
					"geocodigo": geocodigo,
					"metadata": {"type": "Point", "coordinates": list(pixel.coords[0])},
					"timeseries": time_series,
				}

				docs.append(doc)

			if docs:
				result = update_points_time_series(db, docs)

				docs_length = len(docs)
				total_docs += docs_length
				polygon_time = time.time() - polygon_start_time
				logger.info(
					f"✅ Atualizados {result.modified_count} documentos de {docs_length}."
				)
				logger.info(f"⏱️  Polígono processado em {polygon_time:.2f} segundos\n")
			else:
				logger.info("⚠️ Nenhum documento para inserir.")

			# Tempo do polígono atual

		except Exception as e:
			logger.info(f"❌ Erro no polígono {i + 1}: {e}")
			polygon_time = time.time() - polygon_start_time
			logger.info(f"⏱️  Tempo até erro: {polygon_time:.2f} segundos")
			break

	# # Calcular tempo tot	al
	end_time = time.time()
	total_time = end_time - start_time
	total_timedelta = timedelta(seconds=total_time)

	logger.info("\n🏁 Processamento concluído!")
	logger.info(f"⏱️  Tempo total de execução: {total_time:.2f} segundos")
	logger.info(f"🕐 Tempo formatado: {str(total_timedelta).split('.')[0]}")
	logger.info(f"📄 Total de documentos atualizados: {total_docs}")
	logger.info(f"🕐 Finalizado às {time.strftime('%H:%M:%S')}")
