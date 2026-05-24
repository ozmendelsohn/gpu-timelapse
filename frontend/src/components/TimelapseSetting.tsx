import { useState } from "react";
import { SpeedMode, OutputFormat } from "../api/client";

interface Props {
  onSubmit: (mode: SpeedMode, value: number, format: OutputFormat) => void;
  disabled: boolean;
}

const FORMATS: { value: OutputFormat; label: string }[] = [
  { value: "mp4", label: "MP4 (H.264 NVENC)" },
  { value: "webm", label: "WebM (VP9)" },
  { value: "gif", label: "GIF (Animated)" },
];

export default function TimelapseSetting({ onSubmit, disabled }: Props) {
  const [mode, setMode] = useState<SpeedMode>("multiplier");
  const [multiplier, setMultiplier] = useState(10);
  const [duration, setDuration] = useState(30);
  const [format, setFormat] = useState<OutputFormat>("mp4");

  function handleSubmit() {
    const value = mode === "multiplier" ? multiplier : duration;
    onSubmit(mode, value, format);
  }

  return (
    <div className="bg-gray-900 rounded-xl p-6 flex flex-col gap-5">
      <h2 className="text-lg font-semibold text-gray-100">Timelapse Settings</h2>

      {/* Mode toggle */}
      <div className="flex rounded-lg overflow-hidden border border-gray-700 w-fit">
        {(["multiplier", "duration"] as SpeedMode[]).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`px-4 py-2 text-sm font-medium transition-colors
              ${mode === m ? "bg-violet-600 text-white" : "text-gray-400 hover:text-gray-200"}`}
          >
            {m === "multiplier" ? "Speed Multiplier" : "Target Duration"}
          </button>
        ))}
      </div>

      {mode === "multiplier" ? (
        <div className="flex flex-col gap-2">
          <div className="flex justify-between text-sm text-gray-400">
            <span>Speed</span>
            <span className="text-violet-400 font-medium">{multiplier}×</span>
          </div>
          <input
            type="range" min={2} max={100} value={multiplier}
            onChange={(e) => setMultiplier(Number(e.target.value))}
            className="w-full accent-violet-500"
          />
          <div className="flex justify-between text-xs text-gray-600">
            <span>2×</span><span>100×</span>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          <label className="text-sm text-gray-400">Target duration (seconds)</label>
          <input
            type="number" min={1} value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 w-36 text-gray-100 focus:outline-none focus:border-violet-500"
          />
        </div>
      )}

      {/* Output format */}
      <div className="flex flex-col gap-2">
        <label className="text-sm text-gray-400">Output format</label>
        <div className="flex gap-2 flex-wrap">
          {FORMATS.map((f) => (
            <button
              key={f.value}
              onClick={() => setFormat(f.value)}
              className={`px-3 py-1.5 rounded-lg text-sm border transition-colors
                ${format === f.value
                  ? "border-violet-500 bg-violet-600/20 text-violet-300"
                  : "border-gray-700 text-gray-400 hover:border-gray-500"}`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={handleSubmit}
        disabled={disabled}
        className="mt-1 bg-violet-600 hover:bg-violet-500 disabled:bg-gray-700 disabled:text-gray-500
          text-white font-semibold py-2.5 rounded-xl transition-colors"
      >
        Create Timelapse
      </button>
    </div>
  );
}
