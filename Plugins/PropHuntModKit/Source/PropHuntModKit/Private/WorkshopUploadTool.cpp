// Workshop upload tool implementation. See WorkshopUploadTool.h.

#include "WorkshopUploadTool.h"

#include "HAL/PlatformProcess.h"
#include "HAL/PlatformMisc.h"
#include "Misc/Paths.h"

#if WITH_PROPHUNT_MODKIT_STEAM
THIRD_PARTY_INCLUDES_START
#include "steam/steam_api.h"
THIRD_PARTY_INCLUDES_END
#endif

DEFINE_LOG_CATEGORY_STATIC(LogPropHuntModKit, Log, All);

#if WITH_PROPHUNT_MODKIT_STEAM
namespace
{
	/** Pump Steam callbacks until an API call completes; copy its result. Returns false on
	 *  timeout or Steam-side failure. Blocking - intended for an editor tool only. */
	bool WaitForApiCall(SteamAPICall_t Handle, void* OutResult, int32 ResultSize, int32 ExpectedCallback, double TimeoutSeconds = 120.0)
	{
		if (!SteamUtils() || Handle == k_uAPICallInvalid)
		{
			return false;
		}
		const double Start = FPlatformTime::Seconds();
		while ((FPlatformTime::Seconds() - Start) < TimeoutSeconds)
		{
			SteamAPI_RunCallbacks();
			bool bFailed = false;
			if (SteamUtils()->IsAPICallCompleted(Handle, &bFailed))
			{
				if (bFailed)
				{
					return false;
				}
				bool bResultFailed = false;
				const bool bGot = SteamUtils()->GetAPICallResult(Handle, OutResult, ResultSize, ExpectedCallback, &bResultFailed);
				return bGot && !bResultFailed;
			}
			FPlatformProcess::Sleep(0.01f);
		}
		return false;
	}

	FWorkshopPublishResult DoUpload(PublishedFileId_t ItemId, bool bIsNew, const FString& ContentFolder, const FString& Title, const FString& Description, const FString& PreviewImagePath, const FString& ChangeNote)
	{
		FWorkshopPublishResult Result;

		ISteamUGC* UGC = SteamUGC();
		if (!UGC || !SteamUtils())
		{
			Result.Message = TEXT("Steam UGC not available (is the Steam client running?).");
			return Result;
		}

		const AppId_t AppId = SteamUtils()->GetAppID();
		const UGCUpdateHandle_t Update = UGC->StartItemUpdate(AppId, ItemId);
		if (Update == k_UGCUpdateHandleInvalid)
		{
			Result.Message = TEXT("StartItemUpdate failed.");
			return Result;
		}

		if (!Title.IsEmpty())
		{
			UGC->SetItemTitle(Update, TCHAR_TO_UTF8(*Title));
		}
		if (!Description.IsEmpty())
		{
			UGC->SetItemDescription(Update, TCHAR_TO_UTF8(*Description));
		}

		const FString AbsContent = FPaths::ConvertRelativePathToFull(ContentFolder);
		if (!AbsContent.IsEmpty())
		{
			UGC->SetItemContent(Update, TCHAR_TO_UTF8(*AbsContent));
		}

		if (!PreviewImagePath.IsEmpty())
		{
			const FString AbsPreview = FPaths::ConvertRelativePathToFull(PreviewImagePath);
			UGC->SetItemPreview(Update, TCHAR_TO_UTF8(*AbsPreview));
		}

		const FString Note = ChangeNote.IsEmpty() ? FString(TEXT("Uploaded via PropHunt Mod Kit")) : ChangeNote;
		const SteamAPICall_t Submit = UGC->SubmitItemUpdate(Update, TCHAR_TO_UTF8(*Note));

		SubmitItemUpdateResult_t SubmitResult;
		FMemory::Memzero(&SubmitResult, sizeof(SubmitResult));
		if (!WaitForApiCall(Submit, &SubmitResult, sizeof(SubmitResult), SubmitItemUpdateResult_t::k_iCallback))
		{
			Result.Message = TEXT("SubmitItemUpdate timed out or failed.");
			return Result;
		}

		Result.PublishedFileId = FString::Printf(TEXT("%llu"), ItemId);
		Result.bNeedsLegalAgreement = SubmitResult.m_bUserNeedsToAcceptWorkshopLegalAgreement;

		if (SubmitResult.m_eResult == k_EResultOK)
		{
			Result.bSuccess = true;
			Result.Message = bIsNew ? TEXT("Item published.") : TEXT("Item updated.");
		}
		else
		{
			Result.Message = FString::Printf(TEXT("SubmitItemUpdate returned EResult %d."), static_cast<int32>(SubmitResult.m_eResult));
		}

		if (Result.bNeedsLegalAgreement)
		{
			Result.Message += TEXT(" You must accept the Workshop Legal Agreement on the item's Steam page.");
		}

		UE_LOG(LogPropHuntModKit, Log, TEXT("DoUpload: id=%s success=%d msg=%s"),
			*Result.PublishedFileId, Result.bSuccess ? 1 : 0, *Result.Message);
		return Result;
	}
}
#endif // WITH_PROPHUNT_MODKIT_STEAM

#if WITH_PROPHUNT_MODKIT_STEAM
/** Make SteamAPI usable from the editor. The editor is not launched by Steam, so it has no
 *  app context; point the SDK at our app id via the documented SteamAppId/SteamGameId env
 *  vars (alternative to steam_appid.txt in the CWD) and init the client API. Idempotent. */
static bool EnsureSteamInitialized()
{
	if (SteamUGC() != nullptr && SteamUtils() != nullptr)
	{
		return true;
	}
	FPlatformMisc::SetEnvironmentVar(TEXT("SteamAppId"), TEXT("4133940"));
	FPlatformMisc::SetEnvironmentVar(TEXT("SteamGameId"), TEXT("4133940"));
	SteamAPI_Init();
	return SteamUGC() != nullptr && SteamUtils() != nullptr;
}
#endif

bool UWorkshopUploadTool::IsSteamReady() const
{
#if WITH_PROPHUNT_MODKIT_STEAM
	return EnsureSteamInitialized();
#else
	return false;
#endif
}

FWorkshopPublishResult UWorkshopUploadTool::PublishNewItem(const FString& ContentFolder, const FString& Title, const FString& Description, const FString& PreviewImagePath)
{
	FWorkshopPublishResult Result;
#if WITH_PROPHUNT_MODKIT_STEAM
	EnsureSteamInitialized();
	ISteamUGC* UGC = SteamUGC();
	if (!UGC || !SteamUtils())
	{
		Result.Message = TEXT("Steam UGC not available (is the Steam client running?).");
		return Result;
	}

	const AppId_t AppId = SteamUtils()->GetAppID();
	const SteamAPICall_t Create = UGC->CreateItem(AppId, k_EWorkshopFileTypeCommunity);

	CreateItemResult_t CreateResult;
	FMemory::Memzero(&CreateResult, sizeof(CreateResult));
	if (!WaitForApiCall(Create, &CreateResult, sizeof(CreateResult), CreateItemResult_t::k_iCallback))
	{
		Result.Message = TEXT("CreateItem timed out or failed.");
		return Result;
	}
	if (CreateResult.m_eResult != k_EResultOK)
	{
		Result.Message = FString::Printf(TEXT("CreateItem returned EResult %d."), static_cast<int32>(CreateResult.m_eResult));
		return Result;
	}

	Result = DoUpload(CreateResult.m_nPublishedFileId, /*bIsNew*/ true, ContentFolder, Title, Description, PreviewImagePath, FString());
#else
	Result.Message = TEXT("Workshop uploading is only available in a Win64 editor build with Steam.");
#endif
	return Result;
}

FWorkshopPublishResult UWorkshopUploadTool::UpdateExistingItem(const FString& PublishedFileId, const FString& ContentFolder, const FString& Title, const FString& Description, const FString& PreviewImagePath, const FString& ChangeNote)
{
	FWorkshopPublishResult Result;
#if WITH_PROPHUNT_MODKIT_STEAM
	EnsureSteamInitialized();
	const uint64 Id = FCString::Strtoui64(*PublishedFileId, nullptr, 10);
	if (Id == 0)
	{
		Result.Message = TEXT("Invalid PublishedFileId.");
		return Result;
	}
	Result = DoUpload(static_cast<PublishedFileId_t>(Id), /*bIsNew*/ false, ContentFolder, Title, Description, PreviewImagePath, ChangeNote);
#else
	Result.Message = TEXT("Workshop uploading is only available in a Win64 editor build with Steam.");
#endif
	return Result;
}
