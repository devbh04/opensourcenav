'use client';
import { Input } from "@/components/ui/input";
import { Github } from "lucide-react";
import { ShineBorder } from "../magicui/shine-border";
import useTutorialStore from "@/store/tutorialstore";

export function BorderBeamInput() {
  const { url, setUrl } = useTutorialStore();
  
  return (
    <div className="relative w-full max-w-sm sm:max-w-md md:max-w-lg lg:max-w-xl xl:max-w-4xl rounded-md">
        <Github className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4 sm:h-5 sm:w-5" />
      <Input
        type="text"
        placeholder="https://github.com/owner/repository-name"
        className="border-0 w-full pl-10 sm:pl-12 h-10 sm:h-12 text-sm sm:text-base focus-visible:border-ring focus-visible:ring-[0px] focus-visible:shadow-md focus-visible:shadow-gray-500 focus-visible:transition-all focus-visible:duration-400 focus-visible:ease-in-out"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        aria-label="GitHub Repository URL"
      />
      <ShineBorder shineColor={["#A07CFE", "#FE8FB5", "#FFBE7B"]} />
    </div>
  );
}
