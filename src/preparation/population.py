from src.config.config import Config
from src.core.config import settings
from src.db.db import Database
from src.utils.utils import print_info


class PopulationPreparation:
    def __init__(self, db: Database, region: str):
        self.db = db
        self.region = region
        # Get config for population
        self.config = Config("population", region)
        self.schema = self.config.preparation['schema']

    def disaggregate_population(self, sub_study_area_id: int):
        """Disaggregate population for sub study area

        Args:
            sub_study_area_id (int): ID of sub study area
        """

        print_info(f"Disaggregate population for sub study area {sub_study_area_id}")
        # Get sum of gross floor area of buildings in sub study area
        sql_sum_gross_floor_area = f"""
            SELECT SUM(gross_floor_area_residential) AS sum_gross_floor_area
            FROM {self.schema}.building b, {self.schema}.sub_study_area s
            WHERE s.id = {sub_study_area_id}
            AND ST_Intersects(b.geom, s.geom)
            AND ST_Intersects(ST_CENTROID(b.geom), s.geom)
            AND residential_status = 'with_residents'
        """
        sum_gross_floor_area = self.db.select(sql_sum_gross_floor_area)[0][0]

        if sum_gross_floor_area is None:
            return

        sql_disaggregate_population = f"""
            INSERT INTO temporal.population (population, building_id, geom, sub_study_area_id)
            SELECT CASE WHEN {sum_gross_floor_area}::float * s.population != 0 
            THEN gross_floor_area_residential::float / {sum_gross_floor_area}::float * s.population::float 
            ELSE 0 END AS population, 
            b.id, ST_CENTROID(b.geom), s.id 
            FROM {self.schema}.building b, {self.schema}.sub_study_area s
            WHERE s.id = {sub_study_area_id}
            AND ST_Intersects(b.geom, s.geom)
            AND ST_Intersects(ST_CENTROID(b.geom), s.geom)
            AND residential_status = 'with_residents'
        """

        self.db.perform(sql_disaggregate_population)

    def run(self):
        """Run the population preparation."""

        study_area_ids = self.config.preparation['study_area_ids']
        sql_sub_study_area_ids = f"SELECT id FROM {self.schema}.sub_study_area WHERE study_area_id IN ({str(study_area_ids)[1:-1]});"
        sub_study_area_ids = self.db.select(sql_sub_study_area_ids)
        sub_study_area_ids = [id for id, in sub_study_area_ids]

        # Create temporal population table
        sql_create_population_table = f"""
            DROP TABLE IF EXISTS temporal.population;
            CREATE TABLE temporal.population AS
            SELECT * 
            FROM {self.schema}.population
            LIMIT 0;
        """
        self.db.perform(sql_create_population_table)

        # Disaggregate population for each sub study area
        print_info("Disaggregating population for each sub study area.")

        for sub_study_area_id in sub_study_area_ids:
            self.disaggregate_population(sub_study_area_id)

        # Create spatial index on temporary population table
        sql_create_spatial_index = "CREATE INDEX ON temporal.population USING GIST (geom);"
        self.db.perform(sql_create_spatial_index)

        # Drop existing population table
        print_info("Dropping original population table.")

        sql_drop_population_table = f"DROP TABLE IF EXISTS {self.schema}.population;"
        self.db.perform(sql_drop_population_table)

        # Create final population table after joining with muncipality and county data
        print_info("Creating final population table after joining with municipality and county data.")

        sql_join_and_create_final_population_table = f"""
            CREATE TABLE {self.schema}.population AS
            SELECT p.population, c.gemeindeschlüssel_ags AS ags_gemeinde,
                LEFT(c.gemeindeschlüssel_ags, 5) AS ags_landkreis, building_id,
                sub_study_area_id, p.geom
            FROM temporal.population p,
                germany_municipalities c
            WHERE ST_intersects(p.geom, c.geom);
        """
        self.db.perform(sql_join_and_create_final_population_table)

        sql_create_final_indexes = f"""
            ALTER TABLE {self.schema}.population ADD PRIMARY KEY (building_id);
            CREATE INDEX ON {self.schema}.population USING GIST (geom);
        """
        self.db.perform(sql_create_final_indexes)


def prepare_population(region: str):
    db_rd = Database(settings.RAW_DATABASE_URI)
    PopulationPreparation(db=db_rd, region=region).run()
    print_info("Finished population preparation.")


if __name__ == "__main__":
    prepare_population("de")
