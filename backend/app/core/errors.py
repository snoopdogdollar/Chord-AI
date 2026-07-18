class ChordAIError(Exception):
    code = "INTERNAL_SERVER_ERROR"
    status_code = 500

    def __init__(self, message: str | None = None):
        self.message = message or "Unexpected server error"
        super().__init__(self.message)


class InvalidAudioFormatError(ChordAIError):
    code = "INVALID_AUDIO_FORMAT"
    status_code = 400


class FileTooLargeError(ChordAIError):
    code = "FILE_TOO_LARGE"
    status_code = 413


class InvalidYouTubeUrlError(ChordAIError):
    code = "INVALID_YOUTUBE_URL"
    status_code = 400


class YouTubeExtractionError(ChordAIError):
    code = "YOUTUBE_EXTRACTION_FAILED"
    status_code = 422


class SongNotFoundError(ChordAIError):
    code = "SONG_NOT_FOUND"
    status_code = 404


class JobNotFoundError(ChordAIError):
    code = "JOB_NOT_FOUND"
    status_code = 404


class ExportNotFoundError(ChordAIError):
    code = "EXPORT_NOT_FOUND"
    status_code = 404


class ProcessingFailedError(ChordAIError):
    code = "PROCESSING_FAILED"
    status_code = 422


class ExportFailedError(ChordAIError):
    code = "EXPORT_FAILED"
    status_code = 422
