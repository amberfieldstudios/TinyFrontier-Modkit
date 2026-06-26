// Editor utility for publishing PropHunt custom maps to the Steam Workshop.
//
// Wraps the Steamworks ISteamUGC create/update/submit flow. Intended to be driven from a
// small editor utility widget or called directly (CallInEditor). The Steam client must be
// running and logged in, and steam_appid.txt (4133940) must sit next to the editor exe.
//
// All Steamworks calls live in the .cpp behind WITH_PROPHUNT_MODKIT_STEAM (Win64).

#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "WorkshopUploadTool.generated.h"

/** Result of a publish/update attempt. */
USTRUCT(BlueprintType)
struct FWorkshopPublishResult
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Workshop")
	bool bSuccess = false;

	/** PublishedFileId of the created/updated item (decimal string). */
	UPROPERTY(BlueprintReadOnly, Category = "Workshop")
	FString PublishedFileId;

	/** Human-readable message (error reason on failure). */
	UPROPERTY(BlueprintReadOnly, Category = "Workshop")
	FString Message;

	/** True if Steam wants the user to accept the Workshop Legal Agreement for this item
	 *  (open the item's Steam page to accept). */
	UPROPERTY(BlueprintReadOnly, Category = "Workshop")
	bool bNeedsLegalAgreement = false;
};

UCLASS(BlueprintType)
class PROPHUNTMODKIT_API UWorkshopUploadTool : public UObject
{
	GENERATED_BODY()

public:
	/** True if Steam + the UGC interface are available right now. */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "PropHunt|Workshop")
	bool IsSteamReady() const;

	/** Create a brand new Workshop item and upload the given content folder.
	 *  @param ContentFolder Absolute path to the folder containing the cooked .pak,
	 *         meta.json and preview image.
	 *  @param Title         Workshop item title.
	 *  @param Description   Workshop item description.
	 *  @param PreviewImagePath Absolute path to a preview image (png/jpg, <1MB).
	 *  Blocks (pumping Steam callbacks) until the upload completes or times out. */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "PropHunt|Workshop")
	FWorkshopPublishResult PublishNewItem(const FString& ContentFolder, const FString& Title, const FString& Description, const FString& PreviewImagePath);

	/** Update an existing Workshop item (re-upload content / metadata).
	 *  @param PublishedFileId Decimal id of the existing item. */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "PropHunt|Workshop")
	FWorkshopPublishResult UpdateExistingItem(const FString& PublishedFileId, const FString& ContentFolder, const FString& Title, const FString& Description, const FString& PreviewImagePath, const FString& ChangeNote);
};
