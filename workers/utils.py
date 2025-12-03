import csv
import json
import os
from typing import Any, Dict, Iterator, List, Optional

import pandas as pd
import requests

def stream_csv(
    path_or_handle: Any,
    chunksize: int = 100_000,
    usecols: Optional[List[str]] = None,
    dtype: Optional[Dict[str, Any]] = None,
    low_memory: bool = False,
    encoding: str = "utf-8",
    sep: str = ",",
    header: Optional[Union[int, str]] = "infer",
    names: Optional[List[str]] = None,
) -> Iterator[pd.DataFrame]:
    """
    Stream a CSV file in chunks.
    path_or_handle: File path (str) or file-like object.
    """
    reader = pd.read_csv(
        path_or_handle,
        chunksize=chunksize,
        dtype=dtype,
        usecols=usecols,
        low_memory=low_memory,
        encoding=encoding,
        sep=sep,
        header=header,
        names=names,
        on_bad_lines="skip",
    )
    for chunk in reader:
        yield chunk

def download_api_pages(source_cfg: Dict) -> Iterator[Dict]:
    url = source_cfg.get("url")
    params = dict(source_cfg.get("params") or {})
    pagination = source_cfg.get("pagination") or {}
    size_param = pagination.get("size_param", "pageSize")
    page_param = pagination.get("page_param", "page")
    max_per_page = int(params.get(size_param, 50000))

    page = int(params.get(page_param, 1))
    while True:
        params[size_param] = max_per_page
        params[page_param] = page
        response = requests.get(url, params=params)
        if response.status_code != 200:
            break
        data = response.json()
        count = 0
        for item in data:
            count = count + 1
            yield item
        if count < max_per_page:
            break
        page = page + 1

def read_hcris_multi(files: Dict[str, str]) -> Dict[str, Iterator[Dict]]:
    def reader(path: str) -> Iterator[Dict]:
        if path is None or not os.path.exists(path):
            return iter([])
        def generate():
            with open(path, "r", encoding="latin-1") as handle:
                csv_reader = csv.reader(handle, delimiter="|")
                header = next(csv_reader)
                cleaned_header = [col.lower() for col in header if col is not None]
                for row in csv_reader:
                    cleaned_row = row[: len(cleaned_header)]
                    yield {cleaned_header[i]: cleaned_row[i] for i in range(len(cleaned_row))}
        return generate()

    return {
        "rpt": reader(files.get("rpt")),
        "nmrc": reader(files.get("nmrc")),
        "alphnmrc": reader(files.get("alphnmrc")),
    }
