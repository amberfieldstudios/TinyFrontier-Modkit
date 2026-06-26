// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

// Tiny RUNTIME module for the Mod Kit. It exists so the prop-tagging type
// (UPropTagAssetUserData) lives in a module that ships in BOTH the packaged game and the
// Mod Kit project, guaranteeing the SAME UClass identity on each side - which is what makes
// a creator-tagged prop readable by the shipping game's disguise check. Keep this module
// free of game logic so the Mod Kit never exposes proprietary gameplay code.
public class PropHuntModKitRuntime : ModuleRules
{
	public PropHuntModKitRuntime(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" });
	}
}
