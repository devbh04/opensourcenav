"use client";
import { Particles } from "@/components/magicui/particles";
import { BorderBeamInput } from "@/components/shared/border-beam-input";
import { AnimatedSubscribeButton } from "@/components/magicui/animated-subscribe-button";
import { CheckIcon, ChevronRightIcon } from "lucide-react";
import { RippleButton } from "@/components/magicui/ripple-button";
import { Textarea } from "@/components/ui/textarea";
import useTutorialStore from "@/store/tutorialstore";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

export default function Tutorial() {
  const router = useRouter();
  const {
    url,
    advConfig,
    setAdvConfig,
    includeFileTypes,
    setIncludeFileTypes,
    excludeFileTypes,
    setExcludeFileTypes,
  } = useTutorialStore();
  const [click, setClick] = useState(false);
  const handleClick = () => {
    setClick(!click);
    setTimeout(() => {
      setClick(!click);
    }, 100);
  }

  const handleGenerateTutorial = async (url: string) => {
    try {
      // Extract GitHub repo information from URL
      const githubMatch = url.match(/github\.com\/([^\/]+)\/([^\/]+)/);
      if (!githubMatch) {
        toast.error("Invalid GitHub URL");
        console.error("Invalid GitHub URL");
        return;
      }
      
      const owner = githubMatch[1];
      const repo = githubMatch[2].replace(/\.git$/, ''); // Remove .git if present
      const repoId = `${owner}--${repo}`;
      
      console.log("Redirecting to:", `/tutorial/repo/${repoId}`);
      
      // Redirect to the repo page
      router.push(`/tutorial/repo/${repoId}`);
    } catch (error) {
      toast.error("Error processing GitHub URL");
      console.error("Error processing GitHub URL:", error);
    }
  };

  return (
    <>
      <div className="relative overflow-hidden h-[480px] w-full">
        <Particles
          className="absolute inset-0"
          quantity={200}
          ease={80}
          color={["#ffffff", "#ff0000", "#00ff00", "#0000ff"]}
          vx={0}
          vy={0}
        />
      </div>
      <div className="max-w-4xl flex flex-col justify-center items-center mx-auto p-4">
        <BorderBeamInput />
        <div className="flex flex-col md:flex-row justify-center items-center mt-8 gap-4">
          <RippleButton
            className={`h-10 w-56 font-semibold transition-all duration-500 ease-in-out ${
              click ? "text-black opacity-100 cursor-pointer transform scale-100 hover:scale-105" : "text-black transform scale-95 hover:scale-105"
            }`}
            rippleColor="#33d6ff"
            onClick={() => {
              setAdvConfig(!advConfig);
              handleClick();
            }}
          >
            Advanced Config
          </RippleButton>
          <AnimatedSubscribeButton
            disabled={!url}
            className={`w-56 h-10 transition-all duration-500 ease-in-out ${
              url
                ? "text-white opacity-100 cursor-pointer transform scale-100 hover:scale-105"
                : "text-gray-400 opacity-50 cursor-not-allowed transform scale-95"
            }`}
            onClick={() => {
              handleGenerateTutorial(url);
            }}
            showBorderBeam={!!url}
          >
            <span className="group inline-flex items-center">
              Generate Tutorial
              <ChevronRightIcon className="ml-1 size-4 transition-transform duration-300 group-hover:translate-x-1" />
            </span>
            <span className="group inline-flex items-center">
              <CheckIcon className="mr-2 size-4" />
              Generating...
            </span>
          </AnimatedSubscribeButton>
        </div>
        <div
          className={`transition-all duration-500 ease-in-out overflow-hidden ${
            advConfig
              ? "max-h-[1000px] opacity-100 transform translate-y-0"
              : "max-h-0 opacity-0 transform -translate-y-4"
          }`}
        >
          <div className="mt-8 w-full max-w-sm sm:max-w-md md:max-w-lg lg:max-w-xl xl:max-w-4xl rounded-md border border-gray-500">
            <p className="text-xs sm:text-sm p-3 sm:p-4 text-gray-400 text-center">
              Customize which files are included or excluded based on patterns
              and size to generate a focused tutorial.
            </p>
            <div className="p-3 sm:p-4 flex flex-col md:flex-row justify-center gap-3 sm:gap-4">
              <div className="w-full md:w-1/2">
                <h1 className="font-semibold text-sm sm:text-base">
                  Include File types
                </h1>
                <p className="text-xs sm:text-sm text-gray-400 mb-2">
                  Comma or newline-separated globs
                </p>
                <Textarea
                  className="mt-2 h-24 sm:h-32 text-xs sm:text-sm"
                  value={includeFileTypes}
                  onChange={(e) => setIncludeFileTypes(e.target.value)}
                />
              </div>
              <div className="w-full md:w-1/2">
                <h1 className="font-semibold text-sm sm:text-base">
                  Exclude File types
                </h1>
                <p className="text-xs sm:text-sm text-gray-400 mb-2">
                  Comma or newline-separated globs
                </p>
                <Textarea
                  className="mt-2 h-24 sm:h-32 text-xs sm:text-sm"
                  value={excludeFileTypes}
                  onChange={(e) => setExcludeFileTypes(e.target.value)}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
