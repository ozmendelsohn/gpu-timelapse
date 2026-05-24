import { useEffect, useState } from "react";
import { getJobStatus, JobStatusResponse } from "../api/client";

interface Props {
  jobId: string;
  onComplete: (res: JobStatusResponse) => void;
}

export default function ProcessingStatus({ jobId, onComplete }: Props) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let active = true;
    async function poll() {
      while (active) {
        try {
          const status = await getJobStatus(jobId);
          if (!active) return; // unmounted while request was in-flight — bail before any state update
          setProgress(status.progress);
          if (status.status === "done" || status.status === "error") {
            onComplete(status);
            return;
          }
        } catch {
          // keep polling on transient network errors
        }
        await new Promise((r) => setTimeout(r, 2000));
      }
    }
    poll();
    return () => { active = false; };
  }, [jobId, onComplete]);

  return (
    <div className="bg-gray-900 rounded-xl p-6 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-100">Processing…</h2>
        <span className="text-violet-400 font-medium text-sm">{progress.toFixed(0)}%</span>
      </div>
      <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-violet-600 to-violet-400 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="text-gray-500 text-sm">Using NVIDIA NVENC GPU acceleration…</p>
    </div>
  );
}
