import { getDownloadUrl } from "../api/client";

const MIME_TYPES: Record<string, string> = {
  mp4: "video/mp4",
  webm: "video/webm",
};

interface Props {
  jobId: string;
  format: string;
  onReset: () => void;
}

export default function VideoPreview({ jobId, format, onReset }: Props) {
  const url = getDownloadUrl(jobId);
  const isVideo = format === "mp4" || format === "webm";

  return (
    <div className="bg-gray-900 rounded-xl p-6 flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-green-400">Done!</h2>
        <button
          onClick={onReset}
          className="text-sm text-gray-400 hover:text-gray-200 transition-colors"
        >
          ← Start over
        </button>
      </div>

      {isVideo ? (
        <video controls className="w-full rounded-lg max-h-96 bg-black">
          <source src={url} type={MIME_TYPES[format]} />
        </video>
      ) : (
        <img src={url} alt="Timelapse GIF" className="w-full rounded-lg" />
      )}

      <a
        href={url}
        download
        className="w-full text-center bg-green-600 hover:bg-green-500 text-white font-semibold
          py-2.5 rounded-xl transition-colors block"
      >
        Download {format.toUpperCase()}
      </a>
    </div>
  );
}
