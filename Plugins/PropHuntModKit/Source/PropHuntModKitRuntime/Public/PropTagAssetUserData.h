// Prop tagging (asset-level): a UAssetUserData you attach to a UStaticMesh ASSET so it
// is recognised as a disguiseable prop everywhere it appears - no per-level setup.
//
// This type lives in the PropHuntModKitRuntime module (shipped inside the Mod Kit AND the
// packaged game) so a prop tagged by a map creator carries the exact same UClass the
// shipping game reads via UDisguiseComponent::CanDisguiseAsMesh().
//
// How to tag a mesh in the editor:
//   1. Open the Static Mesh asset.
//   2. In the Details panel find "Asset User Data", click + and add
//      "Prop Tag (PropHunt)".
//   3. Leave bCanDisguiseAs ticked.
//   4. Enable "Allow CPUAccess" on the same mesh (Details > LOD/General Settings) so the
//      disguise can be copied + painted in a packaged build, then re-cook. The bundled
//      Scripts/fix_prop_cpu_access.py does this in bulk for every tagged prop.

#pragma once

#include "CoreMinimal.h"
#include "Engine/AssetUserData.h"
#include "PropTagAssetUserData.generated.h"

UCLASS(meta = (DisplayName = "Prop Tag (PropHunt)"))
class PROPHUNTMODKITRUNTIME_API UPropTagAssetUserData : public UAssetUserData
{
	GENERATED_BODY()

public:
	/** Hiders may disguise as this mesh. Untick to keep the tag but disable the mesh. */
	UPROPERTY(EditAnywhere, Category = "PropHunt")
	bool bCanDisguiseAs = true;

	/** Optional grouping/label for future UI (e.g. "Furniture", "Barrel"). */
	UPROPERTY(EditAnywhere, Category = "PropHunt")
	FName Category;
};
