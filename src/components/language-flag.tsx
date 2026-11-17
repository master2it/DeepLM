import "flag-icons/css/flag-icons.css";

const FLAGS: Record<string, string> = {
  English: "us",
  Persian: "ir",
  German: "de",
  Arabic: "sa",
  Armenian: "am",
  French: "fr",
  Spanish: "es",
  Italian: "it",
  Turkish: "tr",
  Russian: "ru",
  Japanese: "jp",
  Korean: "kr",
  Chinese: "cn",
};

export function LanguageLabel({ language }: { language: string }) {
  const code = FLAGS[language];
  return (
    <span className="flex items-center gap-2">
      {code ? (
        <span className={`fi fi-${code} shrink-0 rounded-sm`} aria-hidden />
      ) : null}
      <span className="truncate">{language}</span>
    </span>
  );
}
