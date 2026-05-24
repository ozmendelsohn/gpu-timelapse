import { useState, useCallback } from "react";
import VideoUploader from "./components/VideoUploader";
import TimelapseSetting from "./components/TimelapseSetting";
import ProcessingStatus from "./components/ProcessingStatus";
import VideoPreview from "./components/VideoPreview";
import {
  UploadResponse,
  JobStatusResponse,
  OutputFormat,
  SpeedMode,
  startProcessing,
} from "./api/client";

type Stage = "upload" | "configure" | "processing" | "done" | "error";

export default function App() {
  const [stage, setStage] = useState<Stage>("upload");
  const [uploadRes, setUploadRes] = useState<UploadResponse | null>(null);
  const [chosenFormat, setChosenFormat] = useState<OutputFormat>("mp4");
  const [errorMsg, setErrorMsg] = useState("");

  function handleUploaded(res: UploadResponse) {
    setUploadRes(res);
    setStage("configure");
  }

  async function handleProcess(mode: SpeedMode, value: number, format: OutputFormat) {
    if (!uploadRes) return;
    setChosenFormat(format);
    try {
      await startProcessing({ job_id: uploadRes.job_id, mode, value, format });
      setStage("processing");
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : "Failed to start processing");
      setStage("error");
    }
  }

  const handleComplete = useCallback((res: JobStatusResponse) => {
    if (res.status === "done") {
      setStage("done");
    } else {
      setErrorMsg(res.error || "Processing failed");
      setStage("error");
    }
  }, []);

  function reset() {
    setStage("upload");
    setUploadRes(null);
    setErrorMsg("");
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-start px-4 py-12">
      <header className="mb-10 text-center">
        <h1 className="text-3xl font-bold text-white tracking-tight">
          GPU Timelapse Tool
        </h1>
        <p className="text-gray-400 mt-2 text-sm">
          NVIDIA NVENC · FFmpeg · GPU-accelerated
        </p>
      </header>

      <main className="w-full max-w-xl flex flex-col gap-6">
        {/* Step indicator */}
        <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
          {(["upload", "configure", "processing", "done"] as Stage[]).map((s, i) => (
            <span key={s} className="flex items-center gap-2">
              <span className={`font-medium ${stage === s ? "text-violet-400" : ""}`}>
                {i + 1}. {s.charAt(0).toUpperCase() + s.slice(1)}
              </span>
              {i < 3 && <span className="text-gray-700">›</span>}
            </span>
          ))}
        </div>

        {stage === "upload" && (
          <VideoUploader onUploaded={handleUploaded} />
        )}

        {stage === "configure" && uploadRes && (
          <>
            <div className="bg-gray-900/60 rounded-xl px-4 py-3 text-sm text-gray-400 flex justify-between">
              <span className="truncate">{uploadRes.filename}</span>
              <span className="text-gray-500 ml-4 shrink-0">
                {(uploadRes.size / 1024 / 1024).toFixed(1)} MB
              </span>
            </div>
            <TimelapseSetting onSubmit={handleProcess} disabled={false} />
          </>
        )}

        {stage === "processing" && uploadRes && (
          <ProcessingStatus jobId={uploadRes.job_id} onComplete={handleComplete} />
        )}

        {stage === "done" && uploadRes && (
          <VideoPreview jobId={uploadRes.job_id} format={chosenFormat} onReset={reset} />
        )}

        {stage === "error" && (
          <div className="bg-red-950/50 border border-red-700 rounded-xl p-6 flex flex-col gap-4">
            <p className="text-red-400 font-medium">Error</p>
            <p className="text-red-300 text-sm">{errorMsg}</p>
            <button onClick={reset} className="text-sm text-gray-400 hover:text-gray-200 transition-colors self-start">
              ← Try again
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
