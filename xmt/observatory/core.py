INF = 10**7 + 1
FIELD_TYPES = ["enum", "int", "real", "text"]
OBS_TYPES = ["timespan", "log", "event"]


class MissingFieldException(Exception):
    pass


class ExtraFieldException(Exception):
    pass


TYPES_MAP = {"enum": str, "text": str, "int": int, "real": float}


class Observer:
    def __init__(self, spec: dict):
        # store the metadata
        for attr in ["id", "type", "name"]:
            assert attr in spec["metadata"]
        for attr in ["id", "type", "name", "description", "version"]:
            setattr(self, attr, spec["metadata"].get(attr, ""))

        if self.type not in OBS_TYPES:
            raise ValueError(f"Unrecognized observer type {self.type}")

        # flush out the spec
        self.total_spec = spec
        self.spec = spec["fields"]
        self.process_spec()

    def process_spec(self):
        """Also validates the observer specification."""
        for field, fspec in self.spec.items():
            if "required" not in fspec:
                fspec["required"] = True
            if "type" not in fspec:
                fspec["type"] = "text"

            if isinstance(fspec["type"], str):
                splut = fspec["type"].split("[")  # does it have a length constraint?
                if len(splut) == 2:  # yes
                    m, M = [
                        float(x.strip("] ")) for x in splut[-1].split(",")
                    ]  # split, trimming spaces and the final ]
                else:  # none, default to INF
                    m, M = -INF, INF
                tspec = splut[0]  # main specification

                fspec["_type"] = fspec["type"]  # handy for later
                fspec["type"] = {
                    tspec: {
                        "minimum" if fspec["_type"] != "text" else "min_length": m,
                        "maximum" if fspec["_type"] != "text" else "max_length": M,
                    }
                }
            else:
                fspec["_type"] = next(
                    filter(FIELD_TYPES.__contains__, fspec["type"].keys())
                )  # the first type that is mentioned in the fuller spec.

            if fspec["_type"] == "enum":  # adding the 'strict' part
                if "strict" not in fspec["type"]:
                    fspec["type"]["strict"] = True  # enums are strict by default

            if field == "DURATION":
                if not self.type == "timespan":
                    raise ValueError(
                        "This field value is reserved for TIMESPAN observers."
                    )

    def validate(self, inp: dict):
        """
        Validates the input against the (processed) specification.
        """
        for key, val in inp.items():
            try:
                spec = self.spec[key]  # specification for the current key
            except KeyError:
                raise ExtraFieldException(f"Unexpected field {key}")

            if not isinstance(val, TYPES_MAP[spec["_type"]]):
                raise TypeError(f"{key} got unexpected type.")

            # now we have the correct type
            if spec["_type"] == "enum":
                if not spec["type"]["strict"]:
                    continue
                if val not in spec["type"]["enum"]:
                    raise ValueError(f"{key} got a value outside of a strict enum.")
            elif spec["_type"] in ["int", "real"]:
                int_spec = spec["type"][spec["_type"]]
                m, M = int_spec["minimum"], int_spec["maximum"]
                if not m <= val <= M:
                    raise ValueError(f"{key} got a value out of bounds.")
            elif spec["_type"] == "text":
                txt_spec = spec["type"]["text"]
                m, M = txt_spec["min_length"], txt_spec["max_length"]
                if not m <= len(val) <= M:
                    raise ValueError(f"{key} got a text whose length is out of bounds.")
            else:
                raise Exception("Catastrophic failure.")

        for field, fspec in self.spec.items():
            if fspec["required"] and field not in inp:
                raise MissingFieldException(f"Missing {field}.")

        return True  # needless?


if __name__ == "__main__":
    import os
    import yaml

    os.chdir("../../samples")
    spec = yaml.safe_load(open("obspec-mood.yaml"))
    obs = Observer(spec)
