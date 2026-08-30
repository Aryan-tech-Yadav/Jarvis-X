class StepSplitter:
    def split(self, steps, max_files=12):
        result = []
        replacements = {}
        expanded = []
        for step in steps:
            value = dict(step) if isinstance(step, dict) else {"name": str(step)}
            files = int(value.get("estimated_files", 0) or 0)
            if files <= max_files or max_files <= 0:
                expanded.append([value])
                continue
            parts = (files + max_files - 1) // max_files
            pieces = []
            for index in range(parts):
                part = dict(value)
                part["name"] = f"{value['name']} ({index + 1}/{parts})"
                part["estimated_files"] = min(max_files, files - index * max_files)
                part["split_from"] = value["name"]
                if index:
                    part["dependencies"] = [pieces[-1]["name"]]
                pieces.append(part)
            replacements[value["name"]] = pieces[-1]["name"]
            expanded.append(pieces)
        for pieces in expanded:
            for value in pieces:
                if "split_from" not in value:
                    value["dependencies"] = [replacements.get(name, name) for name in value.get("dependencies", ())]
                result.append(value)
        return result
