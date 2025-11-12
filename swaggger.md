- You are a software developer developing a GIS app for urban planning.
- Create a swagger schema based on current schema (attachaed)
    - Remove Study Areas and Tasks section
    - In Projects section, add new endpoint to create and get these component:
        - Streets
        - Clusters
        - Public
        - Subdivision
        - Footprint
        - Building Start
        - Building Max
    - The API path would be `/projects/{id}/{component}`, e.g. `/projects/{id}/streets` 
    - This is the detail for each endpoints:
        - Projects
            - inputs: site polygon geojson and roads linestring geojson. User can upload file or trace on the map. Think of a suitable input format, file upload or as text payload.
            - outputs:
            ```
            {
                project_uuid: <uuid>,
                file: <URL for site.gltf>
            }
            ```
        - Streets
            - output:
                ```
                {
                    file: <URL for streets.gltf>
                }
                ```
        - Clusters
            - output:
                ```
                {
                    file: <URL for clusters.gltf>
                }
                ```
        - Pubic
            - inputs: same as `Streets`
            - output:
                ```
                {
                    file: <URL for public.gltf>
                }
                ```
        - Subdivision
            - output:
                ```
                {
                    file: <URL for subdivision.gltf>
                }
                ```
        - Footprint
            - output:
                ```
                {
                    file: <URL for footprint.gltf>
                }
                ```
        - Building Start
            - output:
                ```
                {
                    file: <URL for building_start.gltf>
                }
                ```
        - Building Max
            - output:
                ```
                {
                    file: <URL for building_max.gltf>,
                    lucky_sheet: {} 
                }
                ```
