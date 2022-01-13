# Prepare POIs
HowTo for preparation of Points of Interest to GOAT database format.  
  
All settings for the subsequent preprocessing of the data are used by the file config.yaml. The "pois" section provides settings for "collection", "preparation" and "fusion" in the corresponding categories. 
In the header of the configuration file there is an attribute "region_pbf" in which as a list the regions for which the data collection and preparation will be performed. 
!!! WARNING Be careful with the choice of region! Too large size and as a consequence, a large amount of data in the OSM for the region may significantly load the operating memory of the computer used and end in failure of the operation.!!!  
## Collection/Preparation
### Collection
In the "collection" subsection, "osm_tags" is specified first. It specifies all kinds of points of interest to be collected from the OSM database. All tags should be correctly categorized by "amenity", "shop", etc. according to the OSM documentation. When placing tags in the wrong category, selected points of interest will not be collected.  
There is an auxiliary function that allows you to automatically assign the desired tags to existing categories. ***  
The next sub-section contains the names of all attributes of the collected objects which will be converted into columns to be placed in the GOAT database. All attributes not specified here will be collected in the "tags" column in json format.  
The subsequent "points", "polygons" and "lines" subsections can be defined as True or False, determining which types of geometries will be collected from the OSM database. !!! WARNING. Due to the existing bug in the "pyrosm" library it is NOT RECOMMENDED to change these settings!!! 
```yaml
VARIABLES_SET:
region_pbf : ["Mittelfranken", ...]
....
pois: 
    collection:
      osm_tags:
        amenity : ["amenity_name1", "amenity_name2", ...]
        shop    : ["shop_name1", "shop_name2", ...]
        ...

      additional_columns: ["name", "brand", ...]
      points    : True # Have to be saved as True
      polygons  : True # Have to be saved as True
      lines     : True # Have to be saved as True

```
### Preparation
The next subcategory "preparation" sets attributes for formatting and re-categorizing the data into the format used by the GOAT.  
All included subcategories allow the processing of raw OSM data by redefining the "operator" value (chain name) for POIs based on the POI category and name. 
In the following subcategories (health_food, hypermarket, supermarket, discount_supermarket, no_end_consumer_store, discount_gym) are the specific names of the network services and the possible "names" used in the OSM. The data is searched and the "amenity" values are changed according to the name of the subcategory. In addition to the points the name "operator" is set according to the defined value. For example: "amenity"="supermarket", "operator"="rewe".
In the sections (organic, chemist, fast_food) the networks are defined in a similar way and the possible used names related to "shop" are redefined in the corresponding "amenity" and the value of the found "operator" is assigned.  
For banks only the "operator" is redefined according to the specified names in the configuration.  
There are 3 sheets in the "sports" subcategory. For all objects in the data is analyzed, if the defined values for "sport" or "leisure" is in leisure_var_add, but the value of "leisure" is not in the list leisure_var_disc and the value of "sport" is not in the list sport_var_disc, then the "amenity" for the object is set to "sport". All original "sport" and "leisure" values are stored in "tags".  
The last subcategory "schools" specifies the configuration for preparing a file with schools for subsequent fusion in the next step. The source file for the preparation from the service "jedeschule". The analysis of the school names takes place and according to the matches the "amenity" schools are assigned according to the category name or are excluded if there is a match with the "exclude" list.  
```yaml
...
    preparation:
      bank: 
        sparkasse : ["kreissparkasse", "sparkasse", "stadtsparkasse"]
      ...
      supermarket: 
        rewe  : ["rewe", "rewe city"]
        ...
      sport:
        sport_var_disc   : [...]
        leisure_var_add  : [...]
        leisure_var_disc : [...]

      schools:
        schule: [...]
        grundschule: [...]
        hauptschule_mittelschule : [...]
        exclude: [...]
...
```

## Fusion
```yaml
...
    fusion:
      table_base  : "pois_bayern"
      rs_set      : ["091620000","095640000", ...]
      fusion_data :
        source:
          geonode:
            doctors_bavaria:
              fusion_type : "replace" or "fuse"
              amenity : "amenity_name" # according OSM documentation
              amenity_set : False or True
              amenity_operator : ("amenity_name","operator_name") # according OSM documentation
              columns2rename : {"old_column_name1" : "new_column_name1", "old_column_name2" : "new_column_name2", ...}
              columns2drop : ["drop_column_name1", "drop_column_name2", ... ]
              column_set_value : {"new_column_name1" : "value1", "new_column_name2" : "value2", ...}
              columns2fuse : ["fuse_column_name1", "fuse_column_name2", ... ]
          geojson:
            dm:
              fusion_type : "replace" or "fuse"
              ...
            mueller:
              ...
...              
```
## 
### Temporary Bug Fix
  Following config set treat the bug issue of pyrosm library
  !!! DO NOT CHANGE !!!
```yaml
...
  bus_stops :
    collection:
      osm_tags: 
        highway          : ["bus_stop"]
        public_transport : ["stop_position", "station"]

      additional_columns : ["name", "brand", "addr:street","addr:housenumber", "addr:postcode", "addr:city", "addr:country", "phone", "website", 
                           "opening_hours", "operator", "origin", "organic", "subway"]
      points   : True
      polygons : True
      lines    : True
    preparation:
    fusion:
```