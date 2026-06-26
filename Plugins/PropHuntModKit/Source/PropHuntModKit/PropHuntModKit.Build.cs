// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class PropHuntModKit : ModuleRules
{
	public PropHuntModKit(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" });
		PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore", "UnrealEd", "Projects" });

		// The Workshop upload tool calls ISteamUGC directly. Steamworks SDK ships with the
		// engine's OnlineSubsystemSteam as the "Steamworks" third-party module. Win64 only;
		// elsewhere the tool compiles to a no-op so the editor still builds.
		if (Target.Platform == UnrealTargetPlatform.Win64)
		{
			AddEngineThirdPartyPrivateStaticDependencies(Target, "Steamworks");
			PublicDefinitions.Add("WITH_PROPHUNT_MODKIT_STEAM=1");
		}
		else
		{
			PublicDefinitions.Add("WITH_PROPHUNT_MODKIT_STEAM=0");
		}
	}
}
