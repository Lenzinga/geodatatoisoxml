# Geodata to ISOXML (ISO 11783)

A simple Python application to convert geodata from various applications, mostly farm managment software, to ISOXML format (ISO 11783).

Available here:
https://geodatatoisoxml.streamlit.app/

## Features

- Convert geodata from agricultural software tools
- Output format complies with the ISOXML (ISO 11783) standard for agricultural machinery (TASKDATA.XML)
- Esay to use Web Interface

## What's been done

- **AMA to ISOXML:** Convert Data from EAMA to ISOXML format. (Austria)
- **ELAN to ISOXML** Convert Data from ELAN to ISOXML format. (NRW, Germany)
- **iBALIS to ISOXML** Convert Data from iBALIS to ISOXML format. (Bavaria, Germany)
    - Uses "Feldstueck" file, not "Nutzung"
- **BEV Austria Single Data to ISOXML** Convert Data from BEV Austria to ISOXML format. (Austria)
    - Searchs for ...GST_V2.shp in the ZIP-file
    - Only upload one ZIP-File, not multiple (not yet supported)
- **FIONA to ISOXML** Convert Data from FIONA to ISOXML format. (BW, Germany)

## What will be done in the future

- **FENDT KML Output to ISOXML** Convert Data from FENDT KML Output to ISOXML format.
- **AGF-Data to ISOXML** Convert Data from AGF to ISOXML format.
- **BEV Austria Data to ISOXML** Convert Data from BEV Austria to ISOXML format. (Austria)
    - Support for multiple ZIP-Files (for downloading fields from multiple KG's)

