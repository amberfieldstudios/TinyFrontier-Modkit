// PropHunt Mod Kit editor module.

#include "Modules/ModuleManager.h"

class FPropHuntModKitModule : public IModuleInterface
{
public:
	virtual void StartupModule() override {}
	virtual void ShutdownModule() override {}
};

IMPLEMENT_MODULE(FPropHuntModKitModule, PropHuntModKit)
