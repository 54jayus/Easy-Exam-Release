from PyQt5.QtCore import QThread, pyqtSignal

from dataclasses import replace

from ...core.factory import GeneratorFactory


class GeneratorThread(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        try:
            self.log.emit("正在初始化任务...")

            def normalize_output_path(path, ext):
                ext = ext.lower()
                lower = path.lower()
                if lower.endswith(".xlsx") and ext == ".pdf":
                    return path[:-5] + ".pdf"
                if lower.endswith(".pdf") and ext == ".xlsx":
                    return path[:-4] + ".xlsx"
                if lower.endswith(ext):
                    return path
                if lower.endswith(".xlsx") or lower.endswith(".pdf"):
                    if ext == ".xlsx":
                        return path[:-5] + ".xlsx"
                    return path[:-4] + ".pdf"
                return path + ext

            export_xlsx = bool(getattr(self.config, "export_xlsx", True))
            export_pdf = bool(getattr(self.config, "export_pdf", False))

            formats = []
            if export_xlsx:
                formats.append("xlsx")
            if export_pdf:
                formats.append("pdf")

            if not formats:
                raise Exception("请至少选择一种输出格式（xlsx 或 pdf）")

            result_paths = []
            steps = len(formats)
            last_progress = -1

            for i, fmt in enumerate(formats):
                def make_callback(step_index):
                    def callback(current, total):
                        if total > 0:
                            local = current / total
                            p = int(((step_index + local) / steps) * 100)
                            if p >= 100:
                                p = 99
                            nonlocal last_progress
                            if p != last_progress:
                                last_progress = p
                                self.progress.emit(p)
                    return callback

                if fmt == "xlsx":
                    output_path = normalize_output_path(self.config.output_path, ".xlsx")
                    step_config = replace(self.config, output_path=output_path, export_xlsx=True, export_pdf=False)
                else:
                    output_path = normalize_output_path(self.config.output_path, ".pdf")
                    step_config = replace(self.config, output_path=output_path, export_xlsx=False, export_pdf=True)

                generator = GeneratorFactory.create_generator(step_config)
                result_path = generator.generate(progress_callback=make_callback(i))
                result_paths.append(result_path)
                self.log.emit(f"文件已保存: {result_path}")

            if last_progress != 100:
                self.progress.emit(100)
            self.log.emit("生成完成！")
            self.finished.emit(result_paths[0])

        except Exception as e:
            self.error.emit(str(e))
